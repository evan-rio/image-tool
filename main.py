# -*- coding: utf-8 -*-
"""OpenCV Image Tool —— 本地图片处理软件

界面文字支持简体中文和英文，启动时自动跟随系统语言，也可以在
「语言」菜单里手动切换（手动选过之后会被记住）。

功能：打开/另存、缩放旋转裁剪、调色滤镜、批量处理、自动增强/边缘检测/人脸检测
"""

import os
import sys
import queue
import time
import threading
import traceback
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont

from lang import (t, APP_NAME, available_languages, current_language,
                  set_language, save_language, init_language)
APP_VERSION = "1.0.8"

SUPPORTED_READ = (".jpg", ".jpeg", ".jfif", ".png", ".bmp", ".webp", ".tif", ".tiff",
                  ".gif", ".jp2", ".avif", ".ico", ".tga", ".qoi", ".ppm", ".pgm",
                  ".pbm", ".pnm", ".pfm", ".hdr", ".sr", ".ras", ".dib", ".pic")
VIEW_MAX = 2000          # 预览用图最大边长，超过则缩放后再调色，保证流畅
HISTORY_LIMIT = 20
FACE_MODEL = "face_detection_yunet_2023mar.onnx"

# macOS 触控/滚轮的规则和 Windows 不同（Windows 滚轮 = 缩放）：
#   - 双指滚动 = 平移图片（符合 Mac 习惯；按住 Shift 则横向平移）
#   - Command + 滚动 = 缩放
# mac 的 delta 量级也小（每格 ±1，且一次手势会连发大量事件），所以缩放按
# delta 大小换算并夹住上限；平移按固定像素步长。数值可按真机手感微调，
# 这套判断只在 mac 上生效，Windows 一行都不受影响。
MAC_WHEEL_BASE = 1.05
MAC_WHEEL_DELTA_CAP = 2.0
MAC_PAN_STEP = 14        # mac 双指滚动每单位 delta 平移的像素数

# 可输出的图片格式：(扩展名, 界面显示名, 质量参数类型或 None, 是否只支持灰度)
IMAGE_FORMATS = [
    ("jpg",  "fmt_jpg",           "jpeg", False),
    ("png",  "fmt_png",                 "png",  False),
    ("webp", "fmt_webp",     "webp", False),
    ("avif", "fmt_avif",   "avif", False),
    ("bmp",  "fmt_bmp",                     None,   False),
    ("tif",  "fmt_tif",             "tiff", False),
    ("jp2",  "fmt_jp2",                  "jp2",  False),
    ("gif",  "fmt_gif",                       None,   False),
    ("ico",  "fmt_ico",                   None,   False),
    ("pdf",  "fmt_pdf",                       None,   False),
    ("tga",  "fmt_tga",                          None,   False),
    ("qoi",  "fmt_qoi",                 None,   False),
    ("hdr",  "fmt_hdr",                     None,   False),
    ("ppm",  "fmt_ppm",                   None,   False),
    ("pgm",  "fmt_pgm",                         None,   True),
    ("pbm",  "fmt_pbm",                       None,   True),
    ("pfm",  "fmt_pfm",                         None,   True),
    ("ras",  "fmt_ras",                     None,   False),
]
FORMAT_EXT = [f[0] for f in IMAGE_FORMATS]
GRAY_ONLY_EXT = {f[0] for f in IMAGE_FORMATS if f[3]}
FORMAT_DESC = {f[0]: f[1] for f in IMAGE_FORMATS}
# 这些格式 OpenCV 的编码器不支持，交给 Pillow 写
PILLOW_EXT = {"avif", "ico", "pdf", "tga", "qoi"}
# 这些格式支持带透明度保存，其余格式存图前要丢掉 alpha 通道
ALPHA_OK = {"png", "webp", "tif", "avif", "qoi", "tga", "jp2"}

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# 水印文字用的字体文件，按平台各准备一份（找不到就会退回内置位图字体，中文会变方块）
if IS_WIN:
    FONT_CANDIDATES = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
elif IS_MAC:
    FONT_CANDIDATES = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
else:
    FONT_CANDIDATES = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


# --------------------------------------------------------------------------
# 通用工具
# --------------------------------------------------------------------------

def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def apply_window_icon(win):
    """设置窗口图标。

    Windows 用 .ico；macOS / Linux 上 iconbitmap 不可用，
    改用 iconphoto 加载 PNG。（macOS 的 Dock 图标来自 .app 包里的 .icns）
    """
    if IS_WIN:
        try:
            ico = resource_path("app.ico")
            if os.path.exists(ico):
                win.iconbitmap(ico)
                return True
        except Exception:
            pass
    try:
        png = resource_path("app_icon.png")
        if os.path.exists(png):
            img = tk.PhotoImage(file=png)
            win.iconphoto(True, img)
            win._icon_photo = img        # 存住引用，否则会被回收成空白图标
            return True
    except Exception:
        pass
    return False


def face_model_path():
    return resource_path(os.path.join("models", FACE_MODEL))


def create_face_detector(size, score_threshold=0.6, nms_threshold=0.3, top_k=5000):
    """创建人脸检测器。

    OpenCV 5 的 ONNX 读取器用的是窄字符路径，遇到中文路径会打不开模型。
    这里在路径含非 ASCII 字符时，临时把工作目录切到模型所在目录，
    用纯英文文件名加载，加载完立刻切回——因为相对路径是按进程的
    工作目录句柄解析的，不受目录名里有没有中文影响。
    """
    path = face_model_path()
    if not os.path.exists(path):
        raise FileNotFoundError(t("face_no_model", path=path))

    if path.isascii():
        return cv2.FaceDetectorYN.create(path, "", size,
                                         score_threshold, nms_threshold, top_k)

    try:
        cwd = os.getcwd()
    except OSError:
        cwd = None
    os.chdir(os.path.dirname(path))
    try:
        return cv2.FaceDetectorYN.create(os.path.basename(path), "", size,
                                         score_threshold, nms_threshold, top_k)
    finally:
        if cwd:
            os.chdir(cwd)


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


def imread_unicode(path):
    """支持中文路径的读图；OpenCV 读不了的格式（AVIF 等）交给 Pillow"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size:
            img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
            if img is not None:
                return img
    except Exception:
        pass
    return _read_with_pillow(path)


def _read_with_pillow(path):
    try:
        pil = Image.open(path)
        pil.load()
        if pil.mode == "RGBA":
            return cv2.cvtColor(np.array(pil), cv2.COLOR_RGBA2BGRA)
        if pil.mode == "RGB":
            return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        if pil.mode in ("L", "1", "I", "F"):
            return np.array(pil)
        if pil.mode == "P":
            return np.array(pil.convert("RGB"))[:, :, ::-1].copy()
        return np.array(pil.convert("RGB"))[:, :, ::-1].copy()
    except Exception:
        return None


def _encode_params(ext, quality):
    """按格式给 OpenCV 编码器不同的质量/压缩参数"""
    ext = ext.lower()
    q = max(1, min(100, int(quality)))
    if ext in (".jpg", ".jpeg", ".jfif"):
        return [cv2.IMWRITE_JPEG_QUALITY, q]
    if ext == ".webp":
        return [cv2.IMWRITE_WEBP_QUALITY, q]
    if ext == ".png":
        # PNG 无质量概念，用压缩级别 0-9 代替
        return [cv2.IMWRITE_PNG_COMPRESSION, max(0, min(9, (100 - q) // 11))]
    if ext in (".tif", ".tiff"):
        # 5 = LZW 无损压缩
        return [cv2.IMWRITE_TIFF_COMPRESSION, 5]
    if ext == ".jp2":
        return [cv2.IMWRITE_JPEG2000_COMPRESSION_X1000, max(1, (110 - q) * 10)]
    return []


def _write_with_cv2(path, img, ext, quality):
    params = _encode_params(ext, quality)
    # 灰度专属格式直接先转灰度，免得 OpenCV 报一次错再重试
    if img.ndim == 3 and ext.lstrip(".") in GRAY_ONLY_EXT:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        ok, buf = cv2.imencode(ext, img, params)
        if not ok or buf is None:
            return False
        buf.tofile(path)
        return True
    except Exception:
        return False


def _write_with_pillow(path, img, ext, quality):
    name = ext.lstrip(".").lower()
    try:
        if img.ndim == 3:
            pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            pil = Image.fromarray(img)
        q = max(1, min(100, int(quality)))

        if name == "avif":
            pil.save(path, format="AVIF", quality=q, speed=6)
        elif name == "ico":
            sizes = [(s, s) for s in (16, 32, 48, 64, 128, 256)]
            pil.save(path, format="ICO", sizes=sizes)
        elif name == "pdf":
            if pil.mode != "RGB":
                pil = pil.convert("RGB")
            pil.save(path, format="PDF", resolution=150.0)
        elif name in ("jpg", "jpeg", "webp"):
            pil.save(path, quality=q)
        else:
            pil.save(path)
        return True
    except Exception:
        return False


def imwrite_unicode(path, img, ext=None, quality=95):
    """支持中文路径的存图（OpenCV 自带的 imwrite 不认中文路径）"""
    ext = (ext or os.path.splitext(path)[1]).lower()
    if not ext.startswith("."):
        ext = "." + ext
    name = ext.lstrip(".")

    if name in PILLOW_EXT:
        return _write_with_pillow(path, img, ext, quality)
    if _write_with_cv2(path, img, ext, quality):
        return True
    # OpenCV 写不了就再试 Pillow
    return _write_with_pillow(path, img, ext, quality)


def to_bgr8(img):
    """把任意读入图统一成 BGR uint8，返回 (bgr, alpha 或 None)"""
    if img is None:
        return None, None
    alpha = None
    if img.dtype == np.uint16:
        img = (img / 257.0).astype(np.uint8)
    elif img.dtype != np.uint8:
        img = np.clip(img, 0, 255).astype(np.uint8)

    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), None
    if img.ndim != 3:
        return None, None

    ch = img.shape[2]
    if ch == 4:
        alpha = img[:, :, 3].copy()
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), alpha
    if ch == 3:
        return img, None
    if ch == 1:
        return cv2.cvtColor(np.ascontiguousarray(img[:, :, 0]), cv2.COLOR_GRAY2BGR), None
    # 2 通道等异常情况：退化成灰度
    return cv2.cvtColor(np.ascontiguousarray(img[:, :, 0]), cv2.COLOR_GRAY2BGR), None


def apply_adjustments(img, p):
    """按参数对图像做亮度/对比度/饱和度/色调/锐化/模糊"""
    out = img.astype(np.float32)

    b = p.get("brightness", 0)
    if b:
        out += b * 2.55

    c = p.get("contrast", 0)
    if c:
        f = (259.0 * (c + 255.0)) / (255.0 * (259.0 - c))
        out = f * (out - 128.0) + 128.0

    t = p.get("warmth", 0)
    if t:
        out[:, :, 0] += t * 0.6      # B
        out[:, :, 2] -= t * 0.6      # R

    out = np.clip(out, 0, 255).astype(np.uint8)

    s = p.get("saturation", 0)
    if s:
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
        if s > 0:
            hsv[:, :, 1] += (255.0 - hsv[:, :, 1]) * (s / 100.0)
        else:
            hsv[:, :, 1] *= (1.0 + s / 100.0)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    bl = p.get("blur", 0)
    if bl > 0:
        k = int(bl / 100.0 * 20) | 1
        if k >= 3:
            out = cv2.GaussianBlur(out, (k, k), 0)

    sh = p.get("sharpen", 0)
    if sh > 0:
        amt = sh / 100.0 * 1.6
        blurred = cv2.GaussianBlur(out, (0, 0), 3)
        out = cv2.addWeighted(out, 1 + amt, blurred, -amt, 0)

    return out


def apply_enhance(img, spec):
    """「画质增强」面板：降噪 -> 锐化 -> 局部对比度 -> 暗角。

    spec 是普通字典（不含 Tk 对象），可安全地在后台线程里调用。
    四个参数都是 0..100 的整数，0 表示跳过该步。
    """
    out = img

    d = int(spec.get("denoise", 0))
    if d > 0:
        h = 3.0 + d / 100.0 * 15.0
        out = cv2.fastNlMeansDenoisingColored(out, None, h, h, 7, 21)

    s = int(spec.get("sharpen", 0))
    if s > 0:
        amt = s / 100.0 * 1.8
        blurred = cv2.GaussianBlur(out, (0, 0), 3)
        out = cv2.addWeighted(out, 1 + amt, blurred, -amt, 0)

    c = int(spec.get("clahe", 0))
    if c > 0:
        lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.0 + c / 100.0 * 4.0, tileGridSize=(8, 8))
        out = cv2.cvtColor(cv2.merge([clahe.apply(l), a, b]), cv2.COLOR_LAB2BGR)

    v = int(spec.get("vignette", 0))
    if v > 0:
        hh, ww = out.shape[:2]
        yy, xx = np.ogrid[:hh, :ww]
        cy, cx = (hh - 1) / 2.0, (ww - 1) / 2.0
        r2 = (((xx - cx) / max(cx, 1.0)) ** 2 + ((yy - cy) / max(cy, 1.0)) ** 2)
        mask = np.clip(1.0 - v / 100.0 * r2, 0.0, 1.0).astype(np.float32)
        out = np.clip(out.astype(np.float32) * mask[:, :, None], 0, 255).astype(np.uint8)

    return out


# --------------------------------------------------------------------------
# 滤镜（一次性应用到整图）
# --------------------------------------------------------------------------

def f_gray(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def f_binary(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, t = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)


def f_invert(img):
    return cv2.bitwise_not(img)


def f_sepia(img):
    k = np.array([[0.272, 0.534, 0.131],
                  [0.349, 0.686, 0.168],
                  [0.393, 0.769, 0.189]])
    out = cv2.transform(img, k)
    return np.clip(out, 0, 255).astype(np.uint8)


def f_vintage(img):
    out = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    out = cv2.GaussianBlur(out, (0, 0), 1.5)
    out = np.clip(out.astype(np.float32) * 1.08 + 12, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_RGB2BGR)


def f_sketch(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inv = 255 - g
    blur = cv2.GaussianBlur(inv, (21, 21), 0)
    dodge = cv2.divide(g, 255 - blur, scale=256)
    return cv2.cvtColor(dodge, cv2.COLOR_GRAY2BGR)


def f_cartoon(img):
    color = cv2.bilateralFilter(img, 9, 75, 75)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.medianBlur(g, 5)
    edges = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 9, 9)
    return cv2.bitwise_and(color, cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR))


def f_emboss(img):
    k = np.array([[-2, -1, 0],
                  [-1, 1, 1],
                  [0, 1, 2]])
    out = cv2.filter2D(img, -1, k)
    return np.clip(out.astype(np.int16) + 128, 0, 255).astype(np.uint8)


def f_pencil(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inv = 255 - gray
    blur = cv2.GaussianBlur(inv, (0, 0), 3)
    out = cv2.divide(gray, 255 - blur, scale=256)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def f_warm(img):
    out = img.astype(np.float32)
    out[:, :, 2] = np.clip(out[:, :, 2] * 1.12 + 10, 0, 255)
    out[:, :, 0] = np.clip(out[:, :, 0] * 0.92, 0, 255)
    return out.astype(np.uint8)


def f_cool(img):
    out = img.astype(np.float32)
    out[:, :, 0] = np.clip(out[:, :, 0] * 1.12 + 10, 0, 255)
    out[:, :, 2] = np.clip(out[:, :, 2] * 0.92, 0, 255)
    return out.astype(np.uint8)


def f_oil(img):
    # 油画（近似）。cv2.xphoto.oilPainting 属于 opencv-contrib，
    # 本仓库只依赖 opencv-python，拿不到，用主包的风格化顶上。
    return cv2.stylization(img, sigma_s=60, sigma_r=0.45)


def f_detail(img):
    return cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)


def f_posterize(img):
    q = 256 // 6
    out = (img.astype(np.uint16) // q) * q + q // 2
    return np.clip(out, 0, 255).astype(np.uint8)


def f_grain(img):
    # 固定随机种子：预览会反复重算，种子不固定的话每帧噪点都变、画面闪烁。
    rng = np.random.default_rng(20240919)
    noise = rng.normal(0.0, 12.0, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def f_dehaze(img):
    f = img.astype(np.float32)
    kernel = np.ones((15, 15), np.uint8)
    dark = cv2.erode(np.min(f, axis=2), kernel)
    A = np.maximum(f.reshape(-1, 3)[int(np.argmax(dark))], 1.0)
    t = 1.0 - 0.85 * cv2.erode(np.min(f / A, axis=2), kernel)
    t = np.clip(t, 0.1, 1.0)[:, :, None]
    return np.clip((f - A) / t + A, 0, 255).astype(np.uint8)


FILTERS = [
    ("gray",      f_gray),
    ("bw",        f_binary),
    ("invert",    f_invert),
    ("sepia",     f_sepia),
    ("vintage",   f_vintage),
    ("sketch",    f_sketch),
    ("pencil",    f_pencil),
    ("cartoon",   f_cartoon),
    ("emboss",    f_emboss),
    ("warm",      f_warm),
    ("cool",      f_cool),
    ("oil",       f_oil),
    ("detail",    f_detail),
    ("posterize", f_posterize),
    ("grain",     f_grain),
    ("dehaze",    f_dehaze),
]

FILTER_MAP = dict(FILTERS)

# 批量处理的下拉框：界面上显示翻译后的文字，但内部一律用这些 ASCII 代号，
# 否则界面切成英文之后，代码里跟中文原文的比较就全都对不上了。
RESIZE_MODES = [("w", "mode_w"), ("h", "mode_h"), ("pct", "mode_pct")]
WM_POSITIONS = [("tl", "pos_tl"), ("tr", "pos_tr"), ("bl", "pos_bl"),
                ("br", "pos_br"), ("c", "pos_c")]


def _display_to_id(text, table, fallback):
    """把下拉框里选中的（翻译过的）文字还原成内部代号。"""
    for ident, key in table:
        if t(key) == text:
            return ident
    return fallback


def resize_mode_values():
    return [t(key) for _, key in RESIZE_MODES]


def wm_position_values():
    return [t(key) for _, key in WM_POSITIONS]


# 批量里可选的一键滤镜；内部代号直接用滤镜 id，「不处理」用 none 占位
BATCH_FILTER_TABLE = [("none", "batch_filter_none")] + \
    [(fid, "filter_" + fid) for fid, _ in FILTERS]


def filter_values():
    return [t(key) for _, key in BATCH_FILTER_TABLE]


def hex_to_bgr(s, default=(0, 0, 255)):
    s = (s or "").lstrip("#")
    try:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return (b, g, r)
    except Exception:
        return default


def detect_faces(img, spec):
    """用 YuNet 检测人脸并画框，返回 (结果图, 人脸数量)。

    只用到 create_face_detector，没有 Tk 对象，可安全跑在后台线程。
    """
    score = max(0.1, min(0.95, float(spec.get("score", 0.6))))
    min_size = max(10, int(spec.get("min_size", 30)))
    thick = max(1, min(12, int(spec.get("thickness", 3))))
    color = hex_to_bgr(spec.get("color", "#FF0000"))
    show_score = bool(spec.get("show_score", True))
    show_landmarks = bool(spec.get("landmarks", False))

    h, w = img.shape[:2]
    scale = 1.0
    m = max(h, w)
    if m > 1280:
        scale = 1280.0 / m
    if scale < 1.0:
        small = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))),
                           interpolation=cv2.INTER_AREA)
    else:
        small = img
    sh, sw = small.shape[:2]

    det = create_face_detector((sw, sh), score_threshold=score)
    det.setInputSize((sw, sh))
    _, faces = det.detect(small)

    out = img.copy()
    n = 0
    if faces is not None:
        for f in faces:
            x, y, bw, bh = (f[0:4] / scale).astype(int)
            # YuNet 的 detect() 没有最小尺寸参数，得自己筛掉过小的人脸
            if min(bw, bh) < min_size:
                continue
            x, y = max(0, x), max(0, y)
            bw, bh = min(w - x, bw), min(h - y, bh)
            if bw <= 0 or bh <= 0:
                continue
            n += 1
            cv2.rectangle(out, (x, y), (x + bw, y + bh), color, thick)
            if show_score:
                cv2.putText(out, f"{float(f[-1]):.2f}", (x, max(14, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, max(1, thick - 1))
            if show_landmarks:
                pts = (f[4:14].reshape(5, 2) / scale).astype(int)
                for px, py in pts:
                    cv2.circle(out, (int(px), int(py)), max(2, thick),
                               (0, 255, 255), -1)
    return out, n


def apply_tool(img, spec, info=None):
    """按「工具描述」对图像做一次性处理。

    spec 是普通字典（滤镜名、Canny 阈值等），不含任何 Tk 对象，
    所以可以安全地在后台线程里调用。返回处理后的新图像；
    附带的说明文字（比如检测到几张人脸）会写进可选的 info 字典。
    """
    if info is None:
        info = {}
    if not spec:
        return img
    kind = spec.get("kind")

    if kind == "filter":
        fn = FILTER_MAP.get(spec.get("name"))
        return fn(img) if fn is not None else img

    if kind == "enhance":
        return apply_enhance(img, spec)

    if kind == "canny":
        lo = int(spec.get("lo", 80))
        hi = int(spec.get("hi", 180))
        if hi <= lo:
            hi = min(255, lo + 60)
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        g = cv2.GaussianBlur(g, (5, 5), 0)
        return cv2.cvtColor(cv2.Canny(g, lo, hi), cv2.COLOR_GRAY2BGR)

    if kind == "auto":
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        out = cv2.cvtColor(cv2.merge([clahe.apply(l), a, b]), cv2.COLOR_LAB2BGR)
        return apply_adjustments(out, {"saturation": 12, "contrast": 8, "sharpen": 25})

    if kind == "face":
        out, n = detect_faces(img, spec)
        info["note"] = t("face_detected", n=n) if n else t("face_none")
        return out

    return img


def tool_label(spec):
    if not spec:
        return ""
    kind = spec.get("kind")
    if kind == "filter":
        return t("filter_" + spec["name"]) if spec.get("name") in FILTER_MAP \
        else t("tool_filter")
    if kind == "canny":
        return t("tool_canny", lo=spec.get("lo"), hi=spec.get("hi"))
    if kind == "auto":
        return t("tool_auto")
    if kind == "enhance":
        return t("tool_enhance")
    if kind == "face":
        return t("tool_face")
    return t("tool_preview")


# --------------------------------------------------------------------------
# 主窗口
# --------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1280x820")
        self.minsize(1000, 680)
        apply_window_icon(self)

        self.work = None            # 全分辨率当前图
        self.view_src = None        # 用于显示的源图（可能已缩小）
        self.preview = None         # 叠加调整参数后的显示图
        self.view_scale = 1.0       # view_src -> work 的缩放比
        self.alpha = None

        self.path = None
        self.zoom = 1.0
        self.tk_img = None
        self._img_item = None           # 画布上的图片对象
        self._disp_size = None          # 图片在画布上的显示尺寸
        self._img_offset = (0, 0)       # 居中后图片左上角相对画布的偏移
        self.crop_mode = False
        self.crop_start = None
        self.crop_rect = None
        self.crop_item = None
        self.persp_mode = False
        self.persp_pts = []             # 透视矫正的四个角点（view_src 坐标）
        self.persp_items = []           # 画布上对应的点/线 item id
        self._preview_job = None
        self._pan_start = None

        self.history = []
        self.hist_idx = -1
        self._loading_hist = False
        self._updating_fields = False
        self._aspect = 1.0

        self.pending_filter = None      # 「滤镜」页待应用的滤镜
        self.pending_adv = None         # 「高级」页待应用的处理（Canny / 自动增强）
        self.pending_enhance = None     # 「增强」页待应用的处理（降噪 / 锐化 / 局部对比度 / 暗角）
        self._preview_gen = 0           # 防止过期的后台结果覆盖新画面
        self._preview_running = False
        self._preview_dirty = False
        self._show_orig = False         # 按住「对比原图」时为 True
        self.save_quality = 95          # 有损格式的保存质量
        self.face_color = "#FF0000"     # 人脸框颜色

        self.params = {
            "brightness": 0, "contrast": 0, "saturation": 0,
            "warmth": 0, "sharpen": 0, "blur": 0,
        }

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self._bind_events()
        self._set_controls_enabled(False)
        self._update_bars()

        self._ui_queue = queue.Queue()
        self._closing = False
        self._poll_id = self.after(50, self._poll_ui_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

    # 后台线程不能直接碰 Tk（Tcl 解释器只允许主线程访问），
    # 统一把要执行的动作丢进队列，由主线程轮询取出执行。
    def post(self, fn):
        if self._closing:
            return
        self._ui_queue.put(fn)

    def _poll_ui_queue(self):
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except tk.TclError:
                    # 控件已经销毁（比如批量窗口被关掉），直接忽略
                    pass
                except Exception as e:
                    # 这里绝不弹模态对话框：后台任务可能连续出错，
                    # 一堆弹窗会把整个程序卡住关不掉。
                    traceback.print_exc()
                    try:
                        self.status.configure(text=t("err_fail", err=e))
                    except Exception:
                        pass
        except queue.Empty:
            pass
        try:
            self._poll_id = self.after(50, self._poll_ui_queue)
        except tk.TclError:
            self._poll_id = None

    def _on_app_close(self):
        """批量任务还在跑的时候，退出前先问一声"""
        bp = getattr(self, "batch_panel", None)
        if bp is not None and getattr(bp, "_running", False):
            if not messagebox.askyesno(
                    APP_NAME,
                    t("quit_batch_msg"),
                    parent=self):
                return
        self.destroy()

    def destroy(self):
        self._closing = True
        # 通知还在跑的批量任务停下，别让它们继续往已销毁的控件上写
        try:
            bp = getattr(self, "batch_panel", None)
            if bp is not None:
                bp.stop_worker()
        except Exception:
            pass
        if getattr(self, "_poll_id", None) is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:
                pass
            self._poll_id = None
        super().destroy()

    # ---------------- 界面搭建 ----------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label=t("menu_open"), accelerator="Ctrl+O", command=self.open_image)
        m_file.add_command(label=t("menu_save"), accelerator="Ctrl+S", command=self.save)
        m_file.add_command(label=t("menu_save_as"), accelerator="Ctrl+Shift+S", command=self.save_as)
        m_file.add_command(label=t("menu_save_quality"), command=self.ask_save_quality)
        m_file.add_separator()
        m_file.add_command(label=t("menu_exit"), command=self.destroy)
        menubar.add_cascade(label=t("menu_file"), menu=m_file)

        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(label=t("menu_undo"), accelerator="Ctrl+Z", command=self.undo)
        m_edit.add_command(label=t("menu_redo"), accelerator="Ctrl+Y", command=self.redo)
        m_edit.add_separator()
        m_edit.add_command(label=t("menu_revert"), command=self.revert)
        menubar.add_cascade(label=t("menu_edit"), menu=m_edit)

        m_geo = tk.Menu(menubar, tearoff=0)
        m_geo.add_command(label=t("menu_rot_ccw"), command=lambda: self.rotate(-90))
        m_geo.add_command(label=t("menu_rot_cw"), command=lambda: self.rotate(90))
        m_geo.add_command(label=t("menu_rot_180"), command=lambda: self.rotate(180))
        m_geo.add_separator()
        m_geo.add_command(label=t("menu_flip_h"), command=lambda: self.flip(1))
        m_geo.add_command(label=t("menu_flip_v"), command=lambda: self.flip(0))
        menubar.add_cascade(label=t("menu_image"), menu=m_geo)

        m_filter = tk.Menu(menubar, tearoff=0)
        for fid, _ in FILTERS:
            m_filter.add_command(label=t("filter_" + fid),
                                 command=lambda n=fid: self.apply_filter(n))
        menubar.add_cascade(label=t("tool_filter"), menu=m_filter)

        m_adv = tk.Menu(menubar, tearoff=0)
        m_adv.add_command(label=t("tool_auto"), command=self.auto_enhance)
        m_adv.add_command(label=t("menu_edge"), command=self.edge_detect)
        m_adv.add_command(label=t("tool_face"), command=self.face_detect)
        menubar.add_cascade(label=t("menu_advanced"), menu=m_adv)

        m_batch = tk.Menu(menubar, tearoff=0)
        m_batch.add_command(label=t("menu_batch_open"), command=self.open_batch)
        menubar.add_cascade(label=t("menu_batch"), menu=m_batch)

        m_lang = tk.Menu(menubar, tearoff=0)
        self._lang_var = tk.StringVar(value=current_language())
        for code, name in available_languages():
            m_lang.add_radiobutton(label=name, value=code, variable=self._lang_var,
                                   command=lambda c=code: self.set_lang(c))
        menubar.add_cascade(label=t("menu_language"), menu=m_lang)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label=t("menu_help_usage"), command=self.show_help)
        m_help.add_command(label=t("menu_about"), command=self.show_about)
        menubar.add_cascade(label=t("menu_help"), menu=m_help)

        self.config(menu=menubar)

    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side="top", fill="x")

        def btn(text, cmd, width=None):
            b = ttk.Button(bar, text=text, command=cmd)
            if width:
                b.configure(width=width)
            b.pack(side="left", padx=2)
            return b

        btn(t("tb_open"), self.open_image)
        btn(t("menu_save"), self.save)
        btn(t("tb_save_as"), self.save_as)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.b_undo = btn(t("menu_undo"), self.undo)
        self.b_redo = btn(t("menu_redo"), self.redo)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.b_fit = btn(t("tb_fit"), self.fit_window)
        btn("1:1", lambda: self.set_zoom(1.0))
        btn(t("tb_zoom_in"), lambda: self.set_zoom(self.zoom * 1.25))
        btn(t("tb_zoom_out"), lambda: self.set_zoom(self.zoom / 1.25))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.b_crop = ttk.Button(bar, text=t("tb_crop"), command=self.toggle_crop)
        self.b_crop.pack(side="left", padx=2)
        self.b_apply_crop = ttk.Button(bar, text=t("tb_crop_apply"), command=self.apply_crop)
        self.b_apply_crop.pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        # 按住不放可以临时看到原图
        self.b_compare = ttk.Button(bar, text=t("tb_compare"))
        self.b_compare.pack(side="left", padx=2)
        self.b_compare.bind("<ButtonPress-1>", lambda e: self._set_show_orig(True))
        self.b_compare.bind("<ButtonRelease-1>", lambda e: self._set_show_orig(False))

    def _build_body(self):
        # 主界面分成两个页签：单张处理 / 批量处理
        self.nb_main = ttk.Notebook(self)
        self.nb_main.pack(side="top", fill="both", expand=True)

        page1 = ttk.Frame(self.nb_main)
        self.nb_main.add(page1, text="     " + t("tab_single") + "     ")

        # 左侧面板
        left = ttk.Frame(page1, width=385, padding=6)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        nb = ttk.Notebook(left)
        nb.pack(fill="both", expand=True)

        nb.add(self._tab_adjust(nb), text=t("tab_adjust"))
        nb.add(self._tab_filter(nb), text=t("tool_filter"))
        nb.add(self._tab_enhance(nb), text=t("tab_enhance"))
        nb.add(self._tab_geometry(nb), text=t("tab_geometry"))
        nb.add(self._tab_advanced(nb), text=t("menu_advanced"))

        # 画布
        right = ttk.Frame(page1)
        right.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(right, bg="#3a3a3a", highlightthickness=0)
        hbar = ttk.Scrollbar(right, orient="horizontal", command=self.canvas.xview)
        vbar = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # 页签2：批量处理（就在主窗口里，不另开窗口）
        self.batch_panel = BatchPanel(self.nb_main, self)
        self.nb_main.add(self.batch_panel, text="     " + t("tab_batch") + "     ")

        self._bind_canvas()

    # ---------------- 语言切换 ----------------

    def set_lang(self, code):
        """用户从菜单里选了语言：记住它，然后重建整个界面。"""
        if code == current_language():
            return
        bp = getattr(self, "batch_panel", None)
        if bp is not None and getattr(bp, "_running", False):
            messagebox.showinfo(APP_NAME, t("lang_busy"), parent=self)
            self._lang_var.set(current_language())
            return
        save_language(code)
        set_language(code)
        self._rebuild_ui()
        self.update_status(t("lang_switched", name=dict(available_languages())[code]))

    def _rebuild_ui(self):
        """重建菜单、工具条、页面和状态栏（图片本身和撤销历史都保留）。"""
        keep = (self.work, self.path, self.alpha, self.history, self.hist_idx,
                self.zoom, self._show_orig)
        try:
            self.config(menu=tk.Menu(self))       # 先摘掉旧菜单栏
        except Exception:
            pass
        for w in self.winfo_children():
            w.destroy()
        self.title(APP_NAME)
        # 画布重建了，画布上的取点模式与叠加层一并复位
        self.crop_mode = False
        self.crop_start = None
        self.crop_item = None
        self.crop_rect = None
        self.persp_mode = False
        self.persp_pts = []
        self.persp_items = []

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        (self.work, self.path, self.alpha, self.history, self.hist_idx,
         self.zoom, self._show_orig) = keep

        self._set_controls_enabled(self.work is not None)
        self._update_bars()
        if self.work is not None:
            self._refresh_view_src()
            self.set_zoom(self.zoom)
            if self.path:
                self.title(f"{os.path.basename(self.path)} — {APP_NAME}")
        self.update_status()

    def show_batch_page(self):
        self.nb_main.select(self.batch_panel)
        self.update_status(t("status_batch_hint"))

    def _slider_row(self, parent, label, key, lo, hi):
        row = ttk.Frame(parent, padding=(0, 3))
        row.pack(fill="x")
        top = ttk.Frame(row)
        top.pack(fill="x")
        ttk.Label(top, text=label, width=12, anchor="w").pack(side="left")
        val = ttk.Label(top, text="0", width=5, anchor="e")
        val.pack(side="right")
        var = tk.DoubleVar(value=0)
        s = ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal",
                      command=lambda v, k=key, lb=val: self._on_slider(k, v, lb))
        s.pack(fill="x")
        self.param_vars[key] = var
        self.param_labels[key] = val
        self.param_scales[key] = s

    def _enh_slider_row(self, parent, label, key, lo, hi):
        """和 _slider_row 同款，但存进 enh_* 容器、走「增强」这一路"""
        row = ttk.Frame(parent, padding=(0, 3))
        row.pack(fill="x")
        top = ttk.Frame(row)
        top.pack(fill="x")
        ttk.Label(top, text=label, width=12, anchor="w").pack(side="left")
        val = ttk.Label(top, text="0", width=5, anchor="e")
        val.pack(side="right")
        var = tk.DoubleVar(value=0)
        s = ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal",
                      command=lambda v, k=key, lb=val: self._on_enhance_slider(k, v, lb))
        s.pack(fill="x")
        self.enh_vars[key] = var
        self.enh_labels[key] = val
        self.enh_scales[key] = s

    def _tab_enhance(self, nb):
        self.enh_vars = {}
        self.enh_labels = {}
        self.enh_scales = {}
        f = ttk.Frame(nb, padding=8)

        ttk.Label(f, text=t("enh_sec_clean"), foreground="#666").pack(anchor="w")
        self._enh_slider_row(f, t("enh_denoise"), "denoise", 0, 100)
        self._enh_slider_row(f, t("enh_sharpen"), "sharpen", 0, 100)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(f, text=t("enh_sec_tone"), foreground="#666").pack(anchor="w")
        self._enh_slider_row(f, t("enh_clahe"), "clahe", 0, 100)
        self._enh_slider_row(f, t("enh_vignette"), "vignette", 0, 100)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        self.b_enh_apply, self.b_enh_cancel = self._apply_row(
            f, t("enh_apply"), lambda: self.apply_slot("enhance"),
            lambda: self.cancel_slot("enhance"), hint=t("enh_hint"))
        return f

    def _tab_adjust(self, nb):
        self.param_vars = {}
        self.param_labels = {}
        self.param_scales = {}
        f = ttk.Frame(nb, padding=8)
        for label, key in [(t("adj_brightness"), "brightness"), (t("adj_contrast"), "contrast"),
                           (t("adj_saturation"), "saturation"), (t("adj_warmth"), "warmth"),
                           (t("adj_sharpen"), "sharpen"), (t("adj_blur"), "blur")]:
            lo, hi = (-100, 100) if key != "blur" else (0, 100)
            if key == "sharpen":
                lo = 0
            self._slider_row(f, label, key, lo, hi)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        self.b_adj_apply, self.b_adj_cancel = self._apply_row(
            f, t("adj_apply"), lambda: self.apply_slot("adjust"),
            lambda: self.cancel_slot("adjust"),
            hint=t("adj_hint"))
        return f

    def _tab_filter(self, nb):
        f = ttk.Frame(nb, padding=8)
        ttk.Label(f, text=t("filter_hint"),
                  foreground="#666", wraplength=290, justify="left").pack(anchor="w")
        grid = ttk.Frame(f, padding=(0, 6))
        grid.pack(fill="x")
        for i, (fid, _) in enumerate(FILTERS):
            ttk.Button(grid, text=t("filter_" + fid),
                       command=lambda n=fid: self.apply_filter(n)).grid(
                row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        self.b_flt_apply, self.b_flt_cancel = self._apply_row(
            f, t("filter_apply"), lambda: self.apply_slot("filter"),
            lambda: self.cancel_slot("filter"))
        return f

    def _tab_geometry(self, nb):
        f = ttk.Frame(nb, padding=8)

        ttk.Label(f, text=t("geo_hint"),
                  foreground="#666", wraplength=290, justify="left").pack(anchor="w")
        ttk.Button(f, text=t("geo_undo"), command=self.undo).pack(fill="x", pady=(6, 4))
        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=4)

        ttk.Label(f, text=t("geo_rotate")).pack(anchor="w")
        row = ttk.Frame(f, padding=(0, 4))
        row.pack(fill="x")
        ttk.Button(row, text="↺ 90°", width=7,
                   command=lambda: self.rotate(-90)).pack(side="left", padx=2)
        ttk.Button(row, text="↻ 90°", width=7,
                   command=lambda: self.rotate(90)).pack(side="left", padx=2)
        ttk.Button(row, text="180°", width=7,
                   command=lambda: self.rotate(180)).pack(side="left", padx=2)

        row2 = ttk.Frame(f, padding=(0, 4))
        row2.pack(fill="x")
        ttk.Button(row2, text=t("menu_flip_h"),
                   command=lambda: self.flip(1)).pack(side="left", padx=2)
        ttk.Button(row2, text=t("menu_flip_v"),
                   command=lambda: self.flip(0)).pack(side="left", padx=2)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text=t("geo_rotate_free")).pack(anchor="w")
        row3 = ttk.Frame(f, padding=(0, 4))
        row3.pack(fill="x")
        self.angle_var = tk.DoubleVar(value=0)
        ttk.Spinbox(row3, from_=-180, to=180, increment=1, width=6,
                    textvariable=self.angle_var).pack(side="left")
        ttk.Button(row3, text=t("geo_rotate"),
                   command=lambda: self.rotate_free(self.angle_var.get())).pack(side="left", padx=4)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text=t("geo_resize")).pack(anchor="w")
        row4 = ttk.Frame(f, padding=(0, 4))
        row4.pack(fill="x")
        ttk.Label(row4, text=t("geo_w")).pack(side="left")
        self.w_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.w_var, width=6).pack(side="left", padx=2)
        ttk.Label(row4, text=t("geo_h")).pack(side="left")
        self.h_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.h_var, width=6).pack(side="left", padx=2)
        self.w_var.trace_add("write", lambda *a: self._ratio_from("w"))
        self.h_var.trace_add("write", lambda *a: self._ratio_from("h"))

        self.lock_ratio = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text=t("geo_lock"), variable=self.lock_ratio).pack(anchor="w")
        ttk.Button(f, text=t("geo_apply_resize"), command=self.apply_resize).pack(fill="x", pady=4)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text=t("geo_crop")).pack(anchor="w")
        ttk.Label(f, text=t("geo_crop_hint"),
                  foreground="#666", wraplength=290, justify="left").pack(anchor="w", pady=2)
        ttk.Button(f, text=t("geo_clear_sel"), command=self.clear_crop).pack(fill="x", pady=2)

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        self.b_persp = ttk.Button(f, text=t("geo_persp"), command=self.toggle_persp)
        self.b_persp.pack(fill="x", pady=2)
        ttk.Label(f, text=t("geo_persp_hint"),
                  foreground="#666", wraplength=290, justify="left").pack(anchor="w", pady=2)
        self.b_apply_persp = ttk.Button(f, text=t("geo_persp_apply"),
                                        command=self.apply_persp)
        self.b_apply_persp.pack(fill="x", pady=2)
        ttk.Button(f, text=t("geo_persp_clear"),
                   command=self.clear_persp).pack(fill="x", pady=2)
        return f

    def _tab_advanced(self, nb):
        f = ttk.Frame(nb, padding=8)

        ttk.Label(f, text=t("adv_group")).pack(anchor="w")
        ttk.Button(f, text=t("adv_auto"),
                   command=self.auto_enhance).pack(fill="x", pady=2)
        ttk.Button(f, text=t("adv_canny"),
                   command=self.edge_detect).pack(fill="x", pady=2)

        ttk.Label(f, text=t("adv_canny_th"), foreground="#666").pack(anchor="w", pady=(6, 0))
        self.canny_low = tk.IntVar(value=80)
        self.canny_high = tk.IntVar(value=180)
        self.canny_low_lbl = ttk.Label(f, text=t("adv_low", v=80))
        self.canny_high_lbl = ttk.Label(f, text=t("adv_high", v=180))
        self.canny_low_lbl.pack(anchor="w")
        ttk.Scale(f, from_=0, to=255, variable=self.canny_low,
                  orient="horizontal").pack(fill="x")
        self.canny_high_lbl.pack(anchor="w")
        ttk.Scale(f, from_=0, to=255, variable=self.canny_high,
                  orient="horizontal").pack(fill="x")

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(f, text=t("tool_face"), foreground="#666").pack(anchor="w")

        row = ttk.Frame(f)
        row.pack(fill="x", pady=(4, 0))
        ttk.Label(row, text=t("face_sensitivity")).pack(side="left")
        self.face_score_lbl = ttk.Label(row, text="0.60", width=5, anchor="e")
        self.face_score_lbl.pack(side="right")
        self.face_score = tk.DoubleVar(value=0.6)
        ttk.Scale(f, from_=0.10, to=0.95, variable=self.face_score,
                  orient="horizontal").pack(fill="x")

        row2 = ttk.Frame(f, padding=(0, 4))
        row2.pack(fill="x")
        ttk.Label(row2, text=t("face_min")).pack(side="left")
        self.face_min = tk.IntVar(value=30)
        ttk.Spinbox(row2, from_=10, to=2000, increment=10, width=5,
                    textvariable=self.face_min).pack(side="left", padx=3)
        ttk.Label(row2, text=t("face_unit_px")).pack(side="left")

        row3 = ttk.Frame(f, padding=(0, 2))
        row3.pack(fill="x")
        ttk.Label(row3, text=t("face_thick")).pack(side="left")
        self.face_thick = tk.IntVar(value=3)
        ttk.Spinbox(row3, from_=1, to=12, width=4,
                    textvariable=self.face_thick).pack(side="left", padx=3)
        ttk.Button(row3, text=t("face_color"),
                   command=self._pick_face_color).pack(side="left", padx=(8, 3))
        self.face_color_swatch = tk.Label(row3, text="   ", background=self.face_color,
                                          relief="solid", borderwidth=1)
        self.face_color_swatch.pack(side="left")

        self.face_show_score = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text=t("face_show_score"),
                        variable=self.face_show_score).pack(anchor="w")
        self.face_landmarks = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text=t("face_landmarks"),
                        variable=self.face_landmarks).pack(anchor="w")

        ttk.Button(f, text=t("face_preview"),
                   command=self.face_detect).pack(fill="x", pady=(6, 2))
        ttk.Label(f, text=t("face_hint"),
                  foreground="#666", wraplength=290,
                  justify="left").pack(anchor="w")

        # 所有参数变化都实时反映到预览上（用变量监听，打字改数值也生效）
        for var in (self.canny_low, self.canny_high):
            var.trace_add("write", lambda *a: self._on_canny_change())
        for var in (self.face_score, self.face_min, self.face_thick,
                    self.face_show_score, self.face_landmarks):
            var.trace_add("write", lambda *a: self._on_face_setting_change())

        ttk.Separator(f, orient="horizontal").pack(fill="x", pady=8)
        self.b_adv_apply, self.b_adv_cancel = self._apply_row(
            f, t("adv_apply"), lambda: self.apply_slot("adv"),
            lambda: self.cancel_slot("adv"))
        return f

    def _on_canny_change(self, *_):
        try:
            lo = int(self.canny_low.get())
            hi = int(self.canny_high.get())
        except (tk.TclError, ValueError):
            return
        self.canny_low_lbl.configure(text=t("adv_low", v=lo))
        self.canny_high_lbl.configure(text=t("adv_high", v=hi))
        if self.pending_adv is not None and self.pending_adv.get("kind") == "canny":
            self.pending_adv["lo"] = lo
            self.pending_adv["hi"] = hi
            self._schedule_preview(150)

    def _apply_row(self, parent, text, on_apply, on_cancel, hint=None):
        """给每个功能区做一套独立的「应用 / 取消」按钮"""
        if hint:
            ttk.Label(parent, text=hint, foreground="#666",
                      wraplength=290, justify="left").pack(anchor="w")
        row = ttk.Frame(parent, padding=(0, 6))
        row.pack(fill="x")
        b_apply = ttk.Button(row, text=text, state="disabled", command=on_apply)
        b_apply.pack(side="left", expand=True, fill="x", padx=2)
        b_cancel = ttk.Button(row, text=t("btn_reset"), state="disabled", command=on_cancel)
        b_cancel.pack(side="left", expand=True, fill="x", padx=2)
        return b_apply, b_cancel

    def _set_show_orig(self, on):
        self._show_orig = bool(on)
        self._render()

    def _set_sliders_enabled(self, on):
        state = "normal" if on else "disabled"
        for w in getattr(self, "param_scales", {}).values():
            try:
                w.configure(state=state)
            except Exception:
                pass

    def _reset_params_silent(self):
        for k in self.params:
            self.params[k] = 0
            if k in getattr(self, "param_vars", {}):
                self.param_vars[k].set(0)
                self.param_labels[k].configure(text="0")

    def _reset_enhance_silent(self):
        """把「增强」页的滑块归零并清掉待处理项"""
        for k, var in getattr(self, "enh_vars", {}).items():
            var.set(0)
            if k in getattr(self, "enh_labels", {}):
                self.enh_labels[k].configure(text="0")
        self.pending_enhance = None

    def _update_bars(self):
        """每个功能区只根据自己的待处理状态启用各自的按钮"""
        def pair(b, c, active):
            st = "normal" if active else "disabled"
            if b is not None:
                b.configure(state=st)
            if c is not None:
                c.configure(state=st)

        pair(getattr(self, "b_adj_apply", None), getattr(self, "b_adj_cancel", None),
             any(self.params.values()))
        pair(getattr(self, "b_flt_apply", None), getattr(self, "b_flt_cancel", None),
             self.pending_filter is not None)
        pair(getattr(self, "b_adv_apply", None), getattr(self, "b_adv_cancel", None),
             self.pending_adv is not None)
        pair(getattr(self, "b_enh_apply", None), getattr(self, "b_enh_cancel", None),
             self.pending_enhance is not None)

    # ---------------- 预览流水线 ----------------
    # 显示效果 = 原图 -> 滤镜 -> 高级处理 -> 画质增强 -> 调色，各区各自独立待应用

    def _schedule_preview(self, delay=40):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(delay, self._recompute_preview)

    def _recompute_preview(self):
        self._preview_job = None
        if self.view_src is None:
            self.preview = None
            self._render()
            return

        filt = dict(self.pending_filter) if self.pending_filter else None
        adv = dict(self.pending_adv) if self.pending_adv else None
        enh = dict(self.pending_enhance) if self.pending_enhance else None
        params = dict(self.params)

        if filt is None and adv is None and enh is None:
            # 只有调色时同步计算，保证拖滑块跟手
            self.preview = (apply_adjustments(self.view_src, params)
                            if any(params.values()) else None)
            self._render()
            self._update_bars()
            return

        if self._preview_running:
            self._preview_dirty = True
            return

        src = self.view_src
        self._preview_gen += 1
        gen = self._preview_gen
        self._preview_running = True
        self._busy(True, t("previewing"))

        def job():
            try:
                img = src
                if filt is not None:
                    img = apply_tool(img, filt)
                if adv is not None:
                    img = apply_tool(img, adv)
                if enh is not None:
                    img = apply_tool(img, enh)
                if any(params.values()):
                    img = apply_adjustments(img, params)
            except Exception as e:
                self.post(lambda: self._fail(e))
                return
            self.post(lambda: self._finish_preview(gen, img))

        threading.Thread(target=job, daemon=True).start()

    def _finish_preview(self, gen, img):
        self._preview_running = False
        if gen == self._preview_gen:
            self.preview = img
            self._busy(False)
            self._render()
            self._update_bars()
        if self._preview_dirty:
            self._preview_dirty = False
            self._schedule_preview(0)

    # ---------------- 各功能区的设置 / 应用 / 取消 ----------------

    def set_filter(self, spec):
        self.pending_filter = dict(spec)
        self._recompute_preview()

    def set_adv(self, spec):
        self.pending_adv = dict(spec)
        self._recompute_preview()

    def set_enhance(self, spec):
        self.pending_enhance = dict(spec)
        self._recompute_preview()

    def apply_slot(self, slot):
        """只把指定功能区预览到的效果固化到全分辨率图像，其它区不受影响"""
        if self.work is None:
            return
        filt = dict(self.pending_filter) if self.pending_filter else None
        adv = dict(self.pending_adv) if self.pending_adv else None
        enh = dict(self.pending_enhance) if self.pending_enhance else None
        params = dict(self.params)

        if slot == "adjust":
            if not any(params.values()):
                self.update_status(t("adj_nothing"))
                return
            label = t("tab_adjust")
        elif slot == "filter":
            if filt is None:
                return
            label = tool_label(filt)
        elif slot == "adv":
            if adv is None:
                return
            label = tool_label(adv)
        elif slot == "enhance":
            if enh is None or not any(enh.get(k, 0) for k in
                                      ("denoise", "sharpen", "clahe", "vignette")):
                self.update_status(t("enh_nothing"))
                return
            label = tool_label(enh)
        else:
            return

        work = self.work
        self._busy(True, t("applying", label=label))

        def job():
            info = {}
            try:
                if slot == "filter":
                    out = apply_tool(work, filt)
                elif slot == "adv":
                    out = apply_tool(work, adv, info)
                elif slot == "enhance":
                    out = apply_tool(work, enh, info)
                else:
                    out = apply_adjustments(work, params)
            except Exception as e:
                self.post(lambda: self._fail(e))
                return
            self.post(lambda: self._finish_apply(out, slot, label, info.get("note")))

        threading.Thread(target=job, daemon=True).start()

    def _finish_apply(self, out, slot, label, note=None):
        self.work = out
        self.push_history()
        # 只清掉刚应用的那一项，其它功能区的预览保持不动
        if slot == "adjust":
            self._reset_params_silent()
        elif slot == "filter":
            self.pending_filter = None
        elif slot == "adv":
            self.pending_adv = None
        elif slot == "enhance":
            self._reset_enhance_silent()
        self._refresh_view_src(clear_pending=False)
        self.fit_window()
        self._busy(False)
        self._recompute_preview()
        self.update_status(t("applied", label=label + (f" ({note})" if note else "")))

    def cancel_slot(self, slot):
        if slot == "adjust":
            self._reset_params_silent()
        elif slot == "filter":
            self.pending_filter = None
        elif slot == "adv":
            self.pending_adv = None
        elif slot == "enhance":
            self._reset_enhance_silent()
        self._recompute_preview()
        self.update_status(t("reset_done"))

    def _build_statusbar(self):
        bar = ttk.Frame(self, padding=(8, 3))
        bar.pack(side="bottom", fill="x")
        self.status = ttk.Label(bar, text=t("status_ready"), anchor="w")
        self.status.pack(side="left")
        self.status_zoom = ttk.Label(bar, text="", anchor="e")
        self.status_zoom.pack(side="right")

    def _bind_events(self):
        """窗口级快捷键。只绑一次，切换语言重建界面时不会重复累加。"""
        self.bind("<Control-o>", lambda e: self.open_image())
        self.bind("<Control-s>", lambda e: self.save())
        self.bind("<Control-S>", lambda e: self.save_as())
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())

    def _bind_canvas(self):
        """画布上的事件。切换语言会重建画布，所以每次建完都要重新绑。"""
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        if IS_MAC:
            # Command + 滚动 = 缩放。个别 Tk 版本不认 Command 修饰符，
            # 绑不上也只是少一种缩放手势，不能连累整个画布初始化。
            for seq in ("<Command-MouseWheel>", "<Control-MouseWheel>"):
                try:
                    self.canvas.bind(seq, self._on_wheel_zoom)
                except tk.TclError:
                    pass
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_resize())

    def _set_controls_enabled(self, on):
        state = "normal" if on else "disabled"
        for name in ("b_undo", "b_redo", "b_fit", "b_crop", "b_apply_crop"):
            w = getattr(self, name, None)
            if w is not None:
                w.configure(state=state)

    # ---------------- 图像载入 / 历史 ----------------

    def open_image(self, path=None):
        if path is None:
            path = filedialog.askopenfilename(
                title=t("dlg_choose_image"),
                filetypes=[(t("ft_images"), "*.jpg *.jpeg *.jfif *.png *.bmp *.webp *.tif *.tiff *.gif"),
                           (t("ft_all"), "*.*")])
        if not path:
            return
        raw = imread_unicode(path)
        if raw is None:
            messagebox.showerror(APP_NAME, t("err_open_image", path=path))
            return
        bgr, alpha = to_bgr8(raw)
        if bgr is None or bgr.size == 0:
            messagebox.showerror(APP_NAME, t("err_empty_image"))
            return

        self.path = path
        self.alpha = alpha
        self._open_snapshot = bgr.copy()
        self.history = []
        self.hist_idx = -1
        self._set_work(bgr)
        self.push_history()
        self.title(f"{os.path.basename(path)} — {APP_NAME}")
        self._set_controls_enabled(True)
        self.update_status(t("opened", path=path))

    def _set_work(self, img):
        self.work = img
        self.reset_adjustments(redraw=False)
        self._refresh_view_src()
        self.fit_window()

    def _refresh_view_src(self, clear_pending=True):
        # 源图换了：在途的预览结果作废
        self._preview_gen += 1
        self._preview_running = False
        self._preview_dirty = False
        if clear_pending:
            self.pending_filter = None
            self.pending_adv = None
            self._reset_params_silent()
            self._reset_enhance_silent()
        self.preview = None
        if getattr(self, "canvas", None) is not None:
            self.clear_persp()          # 源图/缩放变了，旧坐标上的四点失效
        self._update_bars()
        if self.work is None:
            self.view_src = None
            return
        h, w = self.work.shape[:2]
        m = max(h, w)
        if m > VIEW_MAX:
            s = VIEW_MAX / float(m)
            self.view_src = cv2.resize(self.work, (max(1, int(w * s)), max(1, int(h * s))),
                                       interpolation=cv2.INTER_AREA)
        else:
            self.view_src = self.work
        self.view_scale = self.work.shape[1] / float(self.view_src.shape[1])

        self._updating_fields = True
        try:
            self.w_var.set(str(self.work.shape[1]))
            self.h_var.set(str(self.work.shape[0]))
        finally:
            self._updating_fields = False
        self._aspect = self.work.shape[1] / float(self.work.shape[0])

    def _ratio_from(self, which):
        if self._updating_fields or not self.lock_ratio.get():
            return
        try:
            w = float(self.w_var.get())
            h = float(self.h_var.get())
        except ValueError:
            return
        self._updating_fields = True
        try:
            if which == "w" and w > 0:
                self.h_var.set(str(max(1, int(round(w / self._aspect)))))
            elif which == "h" and h > 0:
                self.w_var.set(str(max(1, int(round(h * self._aspect)))))
        finally:
            self._updating_fields = False

    def push_history(self):
        if self._loading_hist or self.work is None:
            return
        self.history = self.history[:self.hist_idx + 1]
        self.history.append(self.work.copy())
        if len(self.history) > HISTORY_LIMIT:
            self.history.pop(0)
        self.hist_idx = len(self.history) - 1

    def undo(self):
        if self.hist_idx <= 0:
            self.update_status(t("hist_earliest"))
            return
        self.hist_idx -= 1
        self._load_hist()

    def redo(self):
        if self.hist_idx >= len(self.history) - 1:
            self.update_status(t("hist_no_redo"))
            return
        self.hist_idx += 1
        self._load_hist()

    def _load_hist(self):
        self._loading_hist = True
        try:
            img = self.history[self.hist_idx].copy()
            self.work = img
            self.reset_adjustments(redraw=False)
            self._refresh_view_src()
            self._render()
            self.update_status()
        finally:
            self._loading_hist = False

    def revert(self):
        if getattr(self, "_open_snapshot", None) is None:
            return
        self.work = self._open_snapshot.copy()
        self.reset_adjustments(redraw=False)
        self._refresh_view_src()
        self.fit_window()
        self.push_history()
        self.update_status(t("reverted"))

    # ---------------- 调色预览 ----------------

    def _on_slider(self, key, value, label):
        v = float(value)
        self.params[key] = v
        label.configure(text=f"{v:.0f}")
        # 有滤镜/高级/增强预览在场时，重算要经过它们，放慢一点防止堆积
        delay = 200 if (self.pending_filter or self.pending_adv
                        or self.pending_enhance) else 40
        self._schedule_preview(delay)

    def _on_enhance_slider(self, key, value, label):
        v = float(value)
        label.configure(text=f"{v:.0f}")
        self.set_enhance(self._enhance_spec())

    def _enhance_spec(self):
        return {"kind": "enhance",
                **{k: int(var.get()) for k, var in self.enh_vars.items()}}

    def reset_adjustments(self, redraw=True):
        self._reset_params_silent()
        self.preview = None
        if redraw:
            self._recompute_preview()

    # ---------------- 几何操作 ----------------

    def rotate(self, angle):
        if self.work is None:
            return
        if angle == 90:
            self.work = cv2.rotate(self.work, cv2.ROTATE_90_CLOCKWISE)
        elif angle == -90:
            self.work = cv2.rotate(self.work, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif angle == 180:
            self.work = cv2.rotate(self.work, cv2.ROTATE_180)
        self._after_geometry(t("rotated", a=angle))

    def rotate_free(self, angle):
        if self.work is None:
            return
        h, w = self.work.shape[:2]
        cx, cy = w / 2.0, h / 2.0
        M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
        M[0, 2] += nw / 2.0 - cx
        M[1, 2] += nh / 2.0 - cy
        border = cv2.BORDER_REPLICATE
        self.work = cv2.warpAffine(self.work, M, (nw, nh), flags=cv2.INTER_CUBIC,
                                   borderMode=border)
        self._after_geometry(t("rotated", a=f"{angle:.1f}"))

    def flip(self, code):
        if self.work is None:
            return
        self.work = cv2.flip(self.work, code)
        self._after_geometry(t("flipped"))

    def apply_resize(self):
        if self.work is None:
            return
        try:
            nw = int(float(self.w_var.get()))
            nh = int(float(self.h_var.get()))
        except ValueError:
            messagebox.showwarning(APP_NAME, t("err_size_num"))
            return
        if nw < 1 or nh < 1:
            messagebox.showwarning(APP_NAME, t("err_size_pos"))
            return
        interp = cv2.INTER_AREA if nw * nh < self.work.shape[0] * self.work.shape[1] else cv2.INTER_CUBIC
        self.work = cv2.resize(self.work, (nw, nh), interpolation=interp)
        self._after_geometry(t("resized", w=nw, h=nh))

    def toggle_crop(self):
        if self.work is None:
            return
        if self.persp_mode:                 # 两者都在画布上取点，互斥
            self.persp_mode = False
            self.clear_persp()
            self.b_persp.configure(text=t("geo_persp"))
        self.crop_mode = not self.crop_mode
        self.b_crop.configure(text=t("tb_crop_exit") if self.crop_mode else t("tb_crop"))
        self.config(cursor="crosshair" if self.crop_mode else "")
        if not self.crop_mode:
            self.clear_crop()
        self.update_status(t("crop_hint_click") if self.crop_mode else t("crop_exited"))

    def clear_crop(self):
        if self.crop_item is not None:
            self.canvas.delete(self.crop_item)
            self.crop_item = None
        self.crop_rect = None

    def apply_crop(self):
        if self.work is None or self.crop_rect is None:
            self.update_status(t("crop_need_sel"))
            return
        x0, y0, x1, y1 = self.crop_rect
        s = self.view_scale
        ix0, iy0 = int(round(x0 * s)), int(round(y0 * s))
        ix1, iy1 = int(round(x1 * s)), int(round(y1 * s))
        ih, iw = self.work.shape[:2]
        ix0, ix1 = max(0, min(ix0, iw - 1)), max(1, min(ix1, iw))
        iy0, iy1 = max(0, min(iy0, ih - 1)), max(1, min(iy1, ih))
        if ix1 - ix0 < 2 or iy1 - iy0 < 2:
            messagebox.showwarning(APP_NAME, t("crop_too_small"))
            return
        self.work = self.work[iy0:iy1, ix0:ix1].copy()
        self.clear_crop()
        self._after_geometry(t("cropped", w=ix1 - ix0, h=iy1 - iy0))

    def _after_geometry(self, msg):
        self.push_history()
        self.reset_adjustments(redraw=False)
        self._refresh_view_src()
        self.fit_window()
        self.update_status(msg)

    # ---------------- 透视矫正 / 拉直 ----------------

    def toggle_persp(self):
        if self.work is None:
            return
        if self.crop_mode:                  # 两者都在画布上取点，互斥
            self.crop_mode = False
            self.clear_crop()
            self.b_crop.configure(text=t("tb_crop"))
        self.persp_mode = not self.persp_mode
        self.b_persp.configure(text=t("geo_persp_exit") if self.persp_mode
                               else t("geo_persp"))
        self.config(cursor="crosshair" if self.persp_mode else "")
        if not self.persp_mode:
            self.clear_persp()
        self.update_status(t("geo_persp_hint") if self.persp_mode
                           else t("crop_exited"))

    def clear_persp(self):
        for it in self.persp_items:
            try:
                self.canvas.delete(it)
            except tk.TclError:
                pass
        self.persp_items = []
        self.persp_pts = []

    def _canvas_to_view(self, event):
        """画布坐标 -> view_src 坐标（与裁剪同一套换算）"""
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        cx, cy = self._clamp_to_image(cx, cy)
        ox, oy = self._img_offset
        return (cx - ox) / self.zoom, (cy - oy) / self.zoom

    def _v2c(self, vx, vy):
        """view_src 坐标 -> 画布坐标"""
        ox, oy = self._img_offset
        return ox + vx * self.zoom, oy + vy * self.zoom

    def _redraw_persp(self):
        for it in self.persp_items:
            try:
                self.canvas.delete(it)
            except tk.TclError:
                pass
        self.persp_items = []
        pts = [self._v2c(vx, vy) for vx, vy in self.persp_pts]
        flat = [c for p in pts for c in p]
        if len(pts) == 4:
            self.persp_items.append(self.canvas.create_polygon(
                *flat, outline="#FFAA00", fill="", width=2))
        elif len(pts) >= 2:
            self.persp_items.append(self.canvas.create_line(
                *flat, fill="#00A8FF", width=2, dash=(4, 2)))
        for x, y in pts:
            self.persp_items.append(self.canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4, fill="#00A8FF",
                outline="#FFFFFF", width=1))

    @staticmethod
    def _order_quad(pts):
        """把四个点重排成 左上/右上/右下/左下，点击顺序随便"""
        s = [p[0] + p[1] for p in pts]
        d = [p[0] - p[1] for p in pts]
        return [pts[s.index(min(s))], pts[d.index(max(d))],
                pts[s.index(max(s))], pts[d.index(min(d))]]

    @staticmethod
    def _quad_ok(src):
        """挡掉重复点 / 共线 / 面积过小。getPerspectiveTransform 对退化输入
        不报错、只给出病态矩阵，所以必须自己先判。"""
        for i in range(4):
            for j in range(i + 1, 4):
                if np.linalg.norm(src[i] - src[j]) <= 2.0:
                    return False
        return abs(cv2.contourArea(src.reshape(-1, 1, 2))) > 100.0

    def apply_persp(self):
        if self.work is None or len(self.persp_pts) != 4:
            self.update_status(t("geo_persp_need4"))
            return
        s = self.view_scale
        ih, iw = self.work.shape[:2]
        src = np.float32([[x * s, y * s] for x, y in self._order_quad(self.persp_pts)])
        src[:, 0] = np.clip(src[:, 0], 0, iw - 1)
        src[:, 1] = np.clip(src[:, 1], 0, ih - 1)
        if not self._quad_ok(src):
            messagebox.showwarning(APP_NAME, t("geo_persp_degenerate"))
            return
        w = int(round(max(np.linalg.norm(src[1] - src[0]),
                          np.linalg.norm(src[2] - src[3]))))
        h = int(round(max(np.linalg.norm(src[3] - src[0]),
                          np.linalg.norm(src[2] - src[1]))))
        if w < 8 or h < 8:
            messagebox.showwarning(APP_NAME, t("geo_persp_degenerate"))
            return
        dst = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        m = cv2.getPerspectiveTransform(src, dst)
        self.work = cv2.warpPerspective(self.work, m, (w, h), flags=cv2.INTER_CUBIC)
        self.clear_persp()
        self._after_geometry(t("geo_persp_done", w=w, h=h))

    # ---------------- 滤镜 / 高级 ----------------

    def apply_filter(self, name):
        """点滤镜只是进入预览，点「应用滤镜」才会真正改图"""
        self.set_filter({"kind": "filter", "name": name})

    def auto_enhance(self):
        self.set_adv({"kind": "auto"})

    def edge_detect(self):
        self.set_adv({"kind": "canny",
                      "lo": int(self.canny_low.get()),
                      "hi": int(self.canny_high.get())})

    def face_detect(self):
        """点「预览人脸检测」只是进入预览，点「应用处理」才画到图上"""
        if self.work is None:
            return
        if not os.path.exists(face_model_path()):
            messagebox.showerror(APP_NAME,
                                 t("face_no_model", path=face_model_path()))
            return
        self.set_adv({
            "kind": "face",
            "score": float(self.face_score.get()),
            "min_size": int(self.face_min.get()),
            "thickness": int(self.face_thick.get()),
            "color": self.face_color,
            "show_score": bool(self.face_show_score.get()),
            "landmarks": bool(self.face_landmarks.get()),
        })

    def _on_face_setting_change(self, *_):
        """拖动人脸检测参数时，如果正在预览就实时重算"""
        if getattr(self, "face_score_lbl", None) is not None:
            try:
                self.face_score_lbl.configure(
                    text=f"{float(self.face_score.get()):.2f}")
            except (tk.TclError, ValueError):
                pass
        if self.pending_adv is not None and self.pending_adv.get("kind") == "face":
            self.face_detect()

    def _pick_face_color(self):
        c = colorchooser.askcolor(color=self.face_color, parent=self)
        if c and c[1]:
            self.face_color = c[1]
            self.face_color_swatch.configure(background=c[1])
            self._on_face_setting_change()

    def _fail(self, err):
        self._busy(False)
        messagebox.showerror(APP_NAME, t("err_fail", err=err))

    def _busy(self, on, msg=None):
        self.config(cursor="watch" if on else "")
        if msg:
            self.update_status(msg)
        self.update_idletasks()

    # ---------------- 显示 ----------------

    def _render(self):
        if self._show_orig:
            img = self.view_src
        else:
            img = self.preview if self.preview is not None else self.view_src
        if img is None:
            self.canvas.delete("img")
            self.tk_img = None
            self._img_item = None
            self._disp_size = None
            self._img_offset = (0, 0)
            return
        h, w = img.shape[:2]
        dw, dh = max(1, int(w * self.zoom)), max(1, int(h * self.zoom))
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        resample = Image.NEAREST if self.zoom >= 2.0 else Image.BILINEAR
        if (dw, dh) != (w, h):
            pil = pil.resize((dw, dh), resample)
        self.tk_img = ImageTk.PhotoImage(pil)
        self.canvas.delete("img")
        self._img_item = self.canvas.create_image(0, 0, anchor="nw",
                                                  image=self.tk_img, tags="img")
        self.canvas.tag_lower("img")
        self._disp_size = (dw, dh)
        self._recenter()
        if self.work is not None:
            wh, ww = self.work.shape[:2]
            self.status_zoom.configure(
                text=t("status_zoom", z=f"{self.zoom * 100:.0f}", w=ww, h=wh))

    def _recenter(self):
        """图片比可视区域小时居中显示：宽图左右居中，高图上下居中，两个方向都居中"""
        if self._img_item is None or self._disp_size is None:
            return
        dw, dh = self._disp_size
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        # 只在图片小于可视区域的那个方向上留边，另一个方向保持 0（照常滚动）
        off_x = max(0, (cw - dw) // 2)
        off_y = max(0, (ch - dh) // 2)
        self._img_offset = (off_x, off_y)
        self.canvas.coords(self._img_item, off_x, off_y)
        self.canvas.configure(scrollregion=(0, 0, max(cw, dw), max(ch, dh)))
        if self.persp_mode and self.persp_pts:
            self._redraw_persp()        # 缩放/居中后按新 offset 重画四点

    MAX_DISPLAY = 12000

    def _max_zoom(self):
        if self.view_src is None:
            return 1.0
        h, w = self.view_src.shape[:2]
        return max(0.02, min(16.0, self.MAX_DISPLAY / float(max(h, w))))

    def set_zoom(self, z):
        if self.view_src is None:
            return
        self.zoom = max(0.02, min(self._max_zoom(), z))
        self._render()

    def fit_window(self):
        if self.view_src is None:
            return
        self.update_idletasks()
        cw = max(50, self.canvas.winfo_width())
        ch = max(50, self.canvas.winfo_height())
        h, w = self.view_src.shape[:2]
        self.zoom = max(0.02, min(self._max_zoom(), cw / float(w), ch / float(h)))
        self._render()

    def _on_canvas_resize(self, _=None):
        self._recenter()

    def _on_wheel(self, event):
        """Windows 上滚轮 = 缩放；macOS 上双指滚动 = 平移（缩放见 _on_wheel_zoom）。"""
        if self.view_src is None:
            return
        if IS_MAC:
            self._pan_by_wheel(event)
            return "break"
        factor = 1.15 if event.delta > 0 else 1 / 1.15
        self.set_zoom(self.zoom * factor)
        return "break"

    def _on_wheel_zoom(self, event):
        """macOS 的 Command/Control + 滚动 = 缩放（双指捏合在 Tk 8.6 上拿不到）。"""
        if self.view_src is None:
            return
        d = max(-MAC_WHEEL_DELTA_CAP, min(MAC_WHEEL_DELTA_CAP, float(event.delta)))
        if d == 0:
            return "break"
        self.set_zoom(self.zoom * MAC_WHEEL_BASE ** d)
        return "break"

    def _pan_by_wheel(self, event):
        """把 mac 的双指滚动映射成画布平移；按住 Shift 则横向平移。"""
        d = float(event.delta)
        if d == 0:
            return
        step = -d * MAC_PAN_STEP
        if event.state & 0x0001:            # Shift -> 横向
            self._scroll_canvas(step, 0)
        else:
            self._scroll_canvas(0, step)

    def _scroll_canvas(self, dx, dy):
        """按像素平移画布视图（不动图片内容、不改缩放）。"""
        try:
            x0, y0, x1, y1 = (float(v)
                              for v in str(self.canvas.cget("scrollregion")).split())
        except (ValueError, TypeError):
            return
        rw, rh = x1 - x0, y1 - y0
        if dx and rw > 0:
            fx = self.canvas.xview()[0]
            self.canvas.xview_moveto(fx + dx / rw)
        if dy and rh > 0:
            fy = self.canvas.yview()[0]
            self.canvas.yview_moveto(fy + dy / rh)

    def _clamp_to_image(self, cx, cy):
        """把画布坐标夹到图片显示区域内（图片居中后四周可能留边）"""
        if self._disp_size is None:
            return cx, cy
        dw, dh = self._disp_size
        ox, oy = self._img_offset
        return (min(max(cx, ox), ox + dw), min(max(cy, oy), oy + dh))

    def _on_press(self, event):
        if self.view_src is None:
            return
        if self.crop_mode:
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            cx, cy = self._clamp_to_image(cx, cy)
            self.crop_start = (cx, cy)
            self.clear_crop()
            self.crop_item = self.canvas.create_rectangle(
                cx, cy, cx, cy, outline="#00A8FF", width=2, dash=(4, 2))
        elif self.persp_mode:
            if len(self.persp_pts) < 4:
                self.persp_pts.append(self._canvas_to_view(event))
                self._redraw_persp()
                self.update_status(t("geo_persp_clicked", n=len(self.persp_pts)))
        else:
            self.canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event):
        if self.view_src is None or self.persp_mode:
            return
        if self.crop_mode and self.crop_start is not None:
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            cx, cy = self._clamp_to_image(cx, cy)
            x0, y0 = self.crop_start
            self.canvas.coords(self.crop_item, x0, y0, cx, cy)
        else:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_release(self, event):
        if self.crop_mode and self.crop_start is not None:
            cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            cx, cy = self._clamp_to_image(cx, cy)
            x0, y0 = self.crop_start
            x0, x1 = sorted((x0, cx))
            y0, y1 = sorted((y0, cy))
            # 画布坐标 -> view_src 坐标（先减掉居中留的边）
            ox, oy = self._img_offset
            vx0, vy0 = (x0 - ox) / self.zoom, (y0 - oy) / self.zoom
            vx1, vy1 = (x1 - ox) / self.zoom, (y1 - oy) / self.zoom
            vh, vw = self.view_src.shape[:2]
            vx0 = max(0.0, min(vx0, vw - 1.0))
            vy0 = max(0.0, min(vy0, vh - 1.0))
            vx1 = max(1.0, min(vx1, float(vw)))
            vy1 = max(1.0, min(vy1, float(vh)))
            self.crop_rect = (vx0, vy0, vx1, vy1)
            self.crop_start = None
            self.update_status(
                t("crop_selected", w=int((x1 - x0) / self.zoom),
                                  h=int((y1 - y0) / self.zoom)))

    # ---------------- 保存 ----------------

    def save(self):
        if self.work is None:
            return
        if not self.path:
            return self.save_as()
        self._write_file(self.path)

    def save_as(self):
        if self.work is None:
            return
        init = os.path.basename(self.path) if self.path else t("untitled")
        types = [(t(key), f"*.{e}") for e, key, _, _ in IMAGE_FORMATS]
        types.append((t("ft_all"), "*.*"))

        cur = os.path.splitext(self.path)[1].lower().lstrip(".") if self.path else ""
        default_ext = cur if cur in FORMAT_EXT else "jpg"

        path = filedialog.asksaveasfilename(
            title=t("tb_save_as"), initialfile=init,
            defaultextension="." + default_ext,
            filetypes=types)
        if not path:
            return
        if self._write_file(path):
            self.path = path
            self.title(f"{os.path.basename(path)} — {APP_NAME}")

    def _write_file(self, path):
        name = os.path.splitext(path)[1].lower().lstrip(".")
        img = self.work
        # 不支持透明的格式要先把 alpha 通道去掉，否则编码会失败
        if name in ALPHA_OK:
            img = self._with_alpha(img)
        ok = imwrite_unicode(path, img, quality=self.save_quality)
        if ok:
            self.update_status(t("saved", path=path))
        else:
            messagebox.showerror(
                APP_NAME, t("save_failed", fmt=name.upper()))
        return ok

    def _with_alpha(self, img):
        if self.alpha is None:
            return img
        if img.shape[:2] != self.alpha.shape[:2]:
            return img
        return np.dstack([img, self.alpha])

    def ask_save_quality(self):
        from tkinter import simpledialog
        q = simpledialog.askinteger(
            t("dlg_quality"), t("quality_hint_raw") % self.save_quality,
            parent=self, initialvalue=self.save_quality, minvalue=1, maxvalue=100)
        if q:
            self.save_quality = int(q)
            self.update_status(t("quality_set", q=self.save_quality))

    # ---------------- 状态 / 帮助 ----------------

    def update_status(self, msg=None):
        if msg:
            self.status.configure(text=msg)
        elif self.work is not None:
            h, w = self.work.shape[:2]
            self.status.configure(text=t("status_size", w=w, h=h,
                                                 c=self.work.shape[2]))

    def show_help(self):
        messagebox.showinfo(
            t("menu_help_usage"),
            t("help"))

    def show_about(self):
        messagebox.showinfo(
            t("menu_about"),
            t("about", name=APP_NAME, ver=APP_VERSION, cv=cv2.__version__))

    # ---------------- 批量处理 ----------------

    def open_batch(self):
        self.show_batch_page()


# --------------------------------------------------------------------------
# 批量处理页 —— 主窗口内的一个页签，不另开窗口
# --------------------------------------------------------------------------

class BatchPanel(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=10)
        self.app = app

        self.src_dir = tk.StringVar()
        self.dst_dir = tk.StringVar()
        self.recursive = tk.BooleanVar(value=True)

        self.do_resize = tk.BooleanVar(value=True)
        self.resize_mode = tk.StringVar(value=t("mode_w"))
        self.resize_value = tk.StringVar(value="1920")

        self.do_convert = tk.BooleanVar(value=False)
        self.target_fmt = tk.StringVar(value="jpg")
        self.quality = tk.IntVar(value=92)

        self.do_watermark = tk.BooleanVar(value=False)
        self.wm_text = tk.StringVar(value=t("wm_default"))
        self.wm_pos = tk.StringVar(value=t("pos_br"))
        self.wm_opacity = tk.IntVar(value=45)
        self.wm_size = tk.IntVar(value=36)
        self.wm_color = "#FFFFFF"

        self.do_filter = tk.BooleanVar(value=False)
        self.filter_name = tk.StringVar(value=t("batch_filter_none"))

        self.do_enhance = tk.BooleanVar(value=False)
        self.enh_denoise = tk.IntVar(value=0)
        self.enh_sharpen = tk.IntVar(value=0)
        self.enh_clahe = tk.IntVar(value=0)
        self.enh_vignette = tk.IntVar(value=0)

        # 任务控制
        self._stop = threading.Event()      # 置位 = 请求停止
        self._pause = threading.Event()     # 置位 = 暂停中
        self._running = False
        self._closed = False
        self._total = 0
        self._done_count = 0

        self._build()
        self._set_running(False)

    def post(self, fn):
        """后台线程一律通过主窗口的队列回到主线程执行；应用要退了就丢弃"""
        if self._closed:
            return
        try:
            self.app.post(fn)
        except Exception:
            pass

    def stop_worker(self):
        """让还在跑的任务停下来（退出程序时调用）"""
        self._closed = True
        self._stop.set()
        self._pause.clear()

    def _alive(self):
        """控件还在不在（程序退出过程中 winfo_exists 本身也可能抛错）"""
        if self._closed:
            return False
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _set_running(self, running):
        self._running = running
        if getattr(self, "btn_run", None) is not None:
            self.btn_run.configure(state="disabled" if running else "normal")
        for b in (getattr(self, "btn_pause", None), getattr(self, "btn_stop", None)):
            if b is not None:
                b.configure(state="normal" if running else "disabled")
        if getattr(self, "btn_pause", None) is not None:
            self.btn_pause.configure(text=t("btn_pause"))
        self.update_status()

    # 下面三个是后台线程经队列回调进来的，必须防着页面已经没了
    def _tick(self, v):
        if not self._alive():
            return
        try:
            self.progress.configure(value=v)
        except tk.TclError:
            pass

    def _log(self, msg):
        if not self._alive():
            return
        try:
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        except tk.TclError:
            pass

    def _done(self, ok, fail, stopped):
        if not self._alive():
            return
        try:
            self._set_running(False)
        except tk.TclError:
            return
        if stopped:
            self._log(t("log_stopped", ok=ok, fail=fail))
            return
        self._log(t("log_finished", ok=ok, fail=fail))
        messagebox.showinfo(t("done_title"), t("done_msg", ok=ok, fail=fail),
                            parent=self)

    def _toggle_pause(self):
        if not self._running:
            return
        if self._pause.is_set():
            self._pause.clear()
            self.btn_pause.configure(text=t("btn_pause"))
            self._log(t("log_resume"))
        else:
            self._pause.set()
            self.btn_pause.configure(text=t("btn_resume"))
            self._log(t("log_paused"))
        self.update_status()

    def _stop_now(self):
        if not self._running:
            return
        self._stop.set()
        self._pause.clear()
        self._log(t("log_stopping"))
        self.btn_pause.configure(state="disabled")

    def update_status(self):
        if not self._alive():
            return
        try:
            if self._pause.is_set():
                self.lbl_state.configure(text=t("state_paused"))
            elif self._running:
                self.lbl_state.configure(
                    text=t("state_running", done=self._done_count, total=self._total))
            else:
                self.lbl_state.configure(text=t("state_ready"))
        except tk.TclError:
            pass

    def _build(self):
        ttk.Label(self,
                  text=t("batch_desc"),
                  foreground="#666").pack(anchor="w", pady=(0, 8))

        # ---- 上半部分：左右两栏 ----
        top = ttk.Frame(self)
        top.pack(fill="x")
        top.columnconfigure(0, weight=1, uniform="col")
        top.columnconfigure(1, weight=1, uniform="col")

        # 左：文件夹
        f1 = ttk.LabelFrame(top, text=t("grp_folders"), padding=10)
        f1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        r = ttk.Frame(f1)
        r.pack(fill="x")
        ttk.Label(r, text=t("lbl_src"), width=9).pack(side="left")
        ttk.Entry(r, textvariable=self.src_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(r, text=t("btn_browse"), command=self.pick_src).pack(side="left", padx=(6, 0))

        r = ttk.Frame(f1, padding=(0, 6))
        r.pack(fill="x")
        ttk.Label(r, text=t("lbl_dst"), width=9).pack(side="left")
        ttk.Entry(r, textvariable=self.dst_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(r, text=t("btn_browse"), command=self.pick_dst).pack(side="left", padx=(6, 0))

        ttk.Checkbutton(f1, text=t("chk_recursive"),
                        variable=self.recursive).pack(anchor="w", pady=(4, 0))

        # 右：处理选项
        f2 = ttk.LabelFrame(top, text=t("grp_ops"), padding=10)
        f2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        r = ttk.Frame(f2)
        r.pack(fill="x")
        ttk.Checkbutton(r, text=t("chk_resize"), variable=self.do_resize).pack(side="left")
        ttk.Combobox(r, textvariable=self.resize_mode, width=11, state="readonly",
                     values=resize_mode_values()).pack(side="left", padx=4)
        ttk.Entry(r, textvariable=self.resize_value, width=8).pack(side="left")
        ttk.Label(r, text=t("unit_px_pct")).pack(side="left", padx=4)

        r = ttk.Frame(f2, padding=(0, 6))
        r.pack(fill="x")
        ttk.Checkbutton(r, text=t("chk_convert"), variable=self.do_convert).pack(side="left")
        ttk.Combobox(r, textvariable=self.target_fmt, width=6, state="readonly",
                     values=FORMAT_EXT).pack(side="left", padx=4)
        self.lbl_fmt = ttk.Label(r, text=t(FORMAT_DESC.get("jpg", "")), foreground="#666")
        self.lbl_fmt.pack(side="left", padx=4)
        self.target_fmt.trace_add("write", lambda *a: self.lbl_fmt.configure(
            text=t(FORMAT_DESC.get(self.target_fmt.get(), ""))))
        ttk.Label(r, text=t("lbl_quality")).pack(side="left", padx=(8, 2))
        ttk.Scale(r, from_=1, to=100, variable=self.quality, orient="horizontal",
                  length=100).pack(side="left")
        self.lbl_q = ttk.Label(r, text="92", width=3)
        self.lbl_q.pack(side="left")
        self.quality.trace_add("write", lambda *a: self.lbl_q.configure(
            text=str(int(self.quality.get()))))

        r = ttk.Frame(f2, padding=(0, 6))
        r.pack(fill="x")
        ttk.Checkbutton(r, text=t("chk_watermark"), variable=self.do_watermark).pack(side="left")
        ttk.Entry(r, textvariable=self.wm_text, width=14).pack(side="left", padx=4)
        ttk.Button(r, text=t("btn_color"), width=6, command=self.pick_color).pack(side="left", padx=4)
        self.lbl_color = ttk.Label(r, text="   ", background=self.wm_color,
                                   relief="solid", borderwidth=1)
        self.lbl_color.pack(side="left")

        r = ttk.Frame(f2, padding=(0, 2))
        r.pack(fill="x")
        ttk.Label(r, text=t("lbl_pos")).pack(side="left", padx=(0, 4))
        ttk.Combobox(r, textvariable=self.wm_pos, width=11, state="readonly",
                     values=wm_position_values()).pack(side="left")
        ttk.Label(r, text=t("lbl_font_size")).pack(side="left", padx=(8, 2))
        ttk.Spinbox(r, from_=8, to=300, textvariable=self.wm_size, width=5).pack(side="left")
        ttk.Label(r, text=t("lbl_opacity")).pack(side="left", padx=(8, 2))
        ttk.Scale(r, from_=0, to=100, variable=self.wm_opacity, orient="horizontal",
                  length=80).pack(side="left")

        # ---- 画质处理（滤镜 / 增强）----
        f2c = ttk.LabelFrame(self, text=t("grp_img_ops"), padding=10)
        f2c.pack(fill="x", pady=(10, 0))
        r = ttk.Frame(f2c, padding=(0, 2))
        r.pack(fill="x")
        ttk.Checkbutton(r, text=t("chk_filter_batch"),
                        variable=self.do_filter).pack(side="left")
        ttk.Combobox(r, textvariable=self.filter_name, width=16, state="readonly",
                     values=filter_values()).pack(side="left", padx=6)

        r = ttk.Frame(f2c, padding=(0, 2))
        r.pack(fill="x")
        ttk.Checkbutton(r, text=t("chk_enhance_batch"),
                        variable=self.do_enhance).pack(side="left")
        for lbl, var in ((t("enh_denoise"), self.enh_denoise),
                         (t("enh_sharpen"), self.enh_sharpen),
                         (t("enh_clahe"), self.enh_clahe),
                         (t("enh_vignette"), self.enh_vignette)):
            ttk.Label(r, text=lbl).pack(side="left", padx=(8, 2))
            ttk.Spinbox(r, from_=0, to=100, textvariable=var, width=4).pack(side="left")

        # ---- 任务控制 ----
        f3 = ttk.LabelFrame(self, text=t("grp_task"), padding=10)
        f3.pack(fill="x", pady=(10, 0))
        self.btn_run = ttk.Button(f3, text=t("btn_start"), width=10, command=self.start)
        self.btn_run.grid(row=0, column=0, padx=(0, 4))
        self.btn_pause = ttk.Button(f3, text=t("btn_pause"), width=8, command=self._toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=4)
        self.btn_stop = ttk.Button(f3, text=t("btn_stop"), width=8, command=self._stop_now)
        self.btn_stop.grid(row=0, column=2, padx=4)
        f3.columnconfigure(3, weight=1)
        self.lbl_state = ttk.Label(f3, text=t("state_ready"), width=16)
        self.lbl_state.grid(row=0, column=4, sticky="e")

        self.progress = ttk.Progressbar(f3, mode="determinate")
        self.progress.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(8, 0))

        # ---- 处理记录 ----
        f4 = ttk.LabelFrame(self, text=t("grp_log"), padding=6)
        f4.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(f4, height=8, state="disabled", wrap="word")
        sb = ttk.Scrollbar(f4, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def pick_src(self):
        d = filedialog.askdirectory(title=t("dlg_choose_src"))
        if d:
            self.src_dir.set(d)
            if not self.dst_dir.get():
                self.dst_dir.set(os.path.join(d, "output"))

    def pick_dst(self):
        d = filedialog.askdirectory(title=t("dlg_choose_dst"))
        if d:
            self.dst_dir.set(d)

    def pick_color(self):
        c = colorchooser.askcolor(color=self.wm_color)
        if c and c[1]:
            self.wm_color = c[1]
            self.lbl_color.configure(background=c[1])

    def start(self):
        src = self.src_dir.get().strip()
        dst = self.dst_dir.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showwarning(t("batch_title"), t("warn_no_src"), parent=self)
            return
        if not dst:
            dst = os.path.join(src, "output")
            self.dst_dir.set(dst)
        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            messagebox.showerror(t("batch_title"), t("err_makedirs", err=e), parent=self)
            return

        files = self.collect(src)
        if not files:
            messagebox.showinfo(t("batch_title"), t("info_no_images"), parent=self)
            return

        if not messagebox.askyesno(t("batch_title"), t("confirm_start", n=len(files)),
                                   parent=self):
            return

        # 重置任务状态
        self._stop.clear()
        self._pause.clear()
        self._total = len(files)
        self._done_count = 0
        self.progress.configure(maximum=len(files), value=0)
        self._log(t("log_start", n=len(files)))
        self._set_running(True)

        cfg = self.snapshot()
        threading.Thread(target=self._run, args=(files, src, dst, cfg),
                         daemon=True).start()

    def collect(self, src):
        out = []
        if self.recursive.get():
            for root, _, names in os.walk(src):
                if os.path.basename(root).lower() == "output":
                    continue
                for n in names:
                    if n.lower().endswith(SUPPORTED_READ):
                        out.append(os.path.join(root, n))
        else:
            for n in os.listdir(src):
                p = os.path.join(src, n)
                if os.path.isfile(p) and n.lower().endswith(SUPPORTED_READ):
                    out.append(p)
        return out

    def snapshot(self):
        return {
            "resize": self.do_resize.get(),
            "mode": _display_to_id(self.resize_mode.get(), RESIZE_MODES, "w"),
            "value": self.resize_value.get(),
            "convert": self.do_convert.get(),
            "fmt": self.target_fmt.get(),
            "quality": int(self.quality.get()),
            "watermark": self.do_watermark.get(),
            "text": self.wm_text.get(),
            "pos": _display_to_id(self.wm_pos.get(), WM_POSITIONS, "br"),
            "opacity": int(self.wm_opacity.get()),
            "size": int(self.wm_size.get()),
            "color": self.wm_color,
            "filter": self.do_filter.get(),
            "filter_name": _display_to_id(self.filter_name.get(), BATCH_FILTER_TABLE, "none"),
            "enhance": self.do_enhance.get(),
            "denoise": int(self.enh_denoise.get()),
            "sharpen": int(self.enh_sharpen.get()),
            "clahe": int(self.enh_clahe.get()),
            "vignette": int(self.enh_vignette.get()),
        }

    def _run(self, files, src, dst, cfg):
        ok = 0
        fail = 0
        stopped = False
        total = len(files)

        for i, fp in enumerate(files, 1):
            # 暂停：在这里空转等待（「继续」会把 _pause 清掉）
            while self._pause.is_set() and not self._stop.is_set():
                time.sleep(0.08)
            if self._stop.is_set():
                stopped = True
                break

            try:
                raw = imread_unicode(fp)
                img, alpha = to_bgr8(raw)
                if img is None:
                    raise ValueError(t("err_read"))

                if cfg["resize"]:
                    img = self._resize(img, cfg)
                img = self._apply_filter(img, cfg)
                img = self._apply_enhance(img, cfg)
                if cfg["watermark"]:
                    img = self._watermark(img, cfg)

                rel = os.path.relpath(fp, src)
                rel_dir = os.path.dirname(rel)
                base = os.path.splitext(os.path.basename(fp))[0]
                ext = "." + cfg["fmt"] if cfg["convert"] else \
                    (os.path.splitext(fp)[1] or ".png").lower()
                if ext == ".jpeg":
                    ext = ".jpg"
                out_dir = os.path.join(dst, rel_dir)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, base + ext)

                # 目标格式支持透明、且原图有透明通道时才带上 alpha
                if (alpha is not None and ext.lstrip(".") in ALPHA_OK
                        and alpha.shape[:2] == img.shape[:2]):
                    img = np.dstack([img, alpha])

                if not imwrite_unicode(out_path, img, ext=ext, quality=cfg["quality"]):
                    raise ValueError(t("err_write"))
                ok += 1
                self.post(lambda m=t("log_ok", i=i, n=total, name=os.path.basename(fp)):
                          self._log(m))
            except Exception as e:
                fail += 1
                self.post(lambda m=t("log_fail", i=i, n=total,
                                    name=os.path.basename(fp), err=e):
                          self._log(m))

            self._done_count = i
            self.post(lambda v=i: self._tick(v))

        self.post(lambda o=ok, f=fail, s=stopped: self._done(o, f, s))

    @staticmethod
    def _apply_filter(img, cfg):
        name = cfg.get("filter_name", "none")
        if not cfg.get("filter") or name == "none" or name not in FILTER_MAP:
            return img
        return apply_tool(img, {"kind": "filter", "name": name})

    @staticmethod
    def _apply_enhance(img, cfg):
        if not cfg.get("enhance"):
            return img
        spec = {"kind": "enhance",
                "denoise": cfg.get("denoise", 0), "sharpen": cfg.get("sharpen", 0),
                "clahe": cfg.get("clahe", 0), "vignette": cfg.get("vignette", 0)}
        if not any(spec[k] for k in ("denoise", "sharpen", "clahe", "vignette")):
            return img
        return apply_tool(img, spec)

    @staticmethod
    def _resize(img, cfg):
        h, w = img.shape[:2]
        try:
            v = float(cfg["value"])
        except ValueError:
            return img
        mode = cfg["mode"]
        if mode == "w":
            nw = max(1, int(v))
            nh = max(1, int(h * nw / w))
        elif mode == "h":
            nh = max(1, int(v))
            nw = max(1, int(w * nh / h))
        else:
            nw = max(1, int(w * v / 100.0))
            nh = max(1, int(h * v / 100.0))
        interp = cv2.INTER_AREA if nw * nh < w * h else cv2.INTER_CUBIC
        return cv2.resize(img, (nw, nh), interpolation=interp)

    @staticmethod
    def _watermark(img, cfg):
        h, w = img.shape[:2]
        overlay = img.copy()
        rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb).convert("RGBA")
        layer = Image.new("RGBA", pil.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        scale = max(0.4, min(w, h) / 1000.0)
        size = max(10, int(cfg["size"] * scale))
        font = load_font(size)
        text = cfg["text"]

        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = len(text) * size, size

        m = max(10, int(min(w, h) * 0.02))
        pos = cfg["pos"]
        if pos == "tl":
            xy = (m, m)
        elif pos == "tr":
            xy = (w - tw - m, m)
        elif pos == "bl":
            xy = (m, h - th - m * 2)
        elif pos == "c":
            xy = ((w - tw) // 2, (h - th) // 2)
        else:
            xy = (w - tw - m, h - th - m * 2)

        col = cfg["color"].lstrip("#")
        try:
            r, g, b = int(col[0:2], 16), int(col[2:4], 16), int(col[4:6], 16)
        except Exception:
            r = g = b = 255
        a = int(255 * cfg["opacity"] / 100.0)

        # 描边提高可读性
        draw.text((xy[0] + 2, xy[1] + 2), text, font=font, fill=(0, 0, 0, a))
        draw.text(xy, text, font=font, fill=(r, g, b, a))

        combined = Image.alpha_composite(pil, layer).convert("RGB")
        return cv2.cvtColor(np.array(combined), cv2.COLOR_RGB2BGR)


def main():
    try:
        cv2.setNumThreads(max(1, (os.cpu_count() or 4) - 1))
    except Exception:
        pass
    # 界面文字用哪种语言：优先用用户上次手动选过的，否则跟随系统
    init_language()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(APP_NAME, err)
        except Exception:
            print(err)
        sys.exit(1)
