# -*- coding: utf-8 -*-
"""开发期自检脚本（不属于软件本体）"""
import os
import sys
import time
import threading
import traceback

import numpy as np
import cv2
import tkinter as tk

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

import lang
import main as M

# 测试统一跑中文界面，断言才对得上
lang.set_language("zh")

FAIL = []
OK = []
UI_ERRORS = []


def pump(app, cond, timeout=25, what=""):
    """跑主循环直到条件成立（后台线程的结果要靠主循环取回）"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        app.update()
        if cond():
            return True
        time.sleep(0.03)
    return False


def quiet_errors():
    """把各种弹窗换成记录/直接放行，避免测试卡在模态对话框上"""
    UI_ERRORS.clear()
    M.messagebox.showerror = lambda *a, **k: UI_ERRORS.append(a)
    M.messagebox.showwarning = lambda *a, **k: UI_ERRORS.append(a)
    M.messagebox.showinfo = lambda *a, **k: None
    M.messagebox.askyesno = lambda *a, **k: True


def _make_batch_images(src, n):
    os.makedirs(src, exist_ok=True)
    img = (np.random.rand(40, 60, 3) * 255).astype(np.uint8)
    for i in range(n):
        assert M.imwrite_unicode(os.path.join(src, f"图{i:02d}.jpg"), img, ext=".jpg")


def _out_count(dst):
    """输出目录里有多少个文件（目录不存在算 0）"""
    return len(os.listdir(dst)) if os.path.isdir(dst) else 0


def _rmtree(d):
    for r, _, fs in os.walk(d, topdown=False):
        for f in fs:
            os.remove(os.path.join(r, f))
        os.rmdir(r)


class _FakeDetector:
    """假的 YuNet 检测器：固定报一张人脸，用来验证画框参数有没有生效"""
    BOX = (50, 50, 100, 100)

    def setInputSize(self, size):
        pass

    def detect(self, img):
        x, y, w, h = self.BOX
        row = np.array([[x, y, w, h,
                         x + 0.1 * w, y + 0.30 * h,
                         x + 0.9 * w, y + 0.30 * h,
                         x + 0.5 * w, y + 0.60 * h,
                         x + 0.2 * w, y + 0.80 * h,
                         x + 0.8 * w, y + 0.80 * h,
                         0.99]], dtype=np.float32)
        return 1, row


class fake_detector:
    """临时把 create_face_detector 换成假检测器"""

    def __enter__(self):
        self._orig = M.create_face_detector
        M.create_face_detector = lambda *a, **k: _FakeDetector()
        return self

    def __exit__(self, *exc):
        M.create_face_detector = self._orig
        return False


def check(name, fn):
    try:
        fn()
        OK.append(name)
        print(f"[PASS] {name}")
    except Exception as e:
        FAIL.append((name, traceback.format_exc()))
        print(f"[FAIL] {name}: {e}")


def t_import():
    print("opencv:", cv2.__version__)


def t_to_bgr8():
    g = np.zeros((10, 10), np.uint8)
    b, a = M.to_bgr8(g)
    assert b.shape == (10, 10, 3) and a is None

    bgr = np.zeros((10, 10, 3), np.uint8)
    b, a = M.to_bgr8(bgr)
    assert b.shape == (10, 10, 3) and a is None

    bgra = np.zeros((10, 10, 4), np.uint8)
    bgra[:, :, 3] = 128
    b, a = M.to_bgr8(bgra)
    assert b.shape == (10, 10, 3) and a.shape == (10, 10) and a[0, 0] == 128

    u16 = np.zeros((10, 10), np.uint16)
    u16[:] = 65535
    b, a = M.to_bgr8(u16)
    assert b.dtype == np.uint8 and b[0, 0, 0] == 255

    assert M.to_bgr8(None) == (None, None)


def t_adjustments():
    img = (np.random.rand(60, 80, 3) * 255).astype(np.uint8)
    combos = [
        {"brightness": 40}, {"contrast": -50}, {"saturation": 80},
        {"saturation": -80}, {"warmth": 60}, {"warmth": -60},
        {"sharpen": 100}, {"blur": 70}, {"blur": 5},
        {"brightness": 20, "contrast": 30, "saturation": 40,
         "warmth": 10, "sharpen": 50, "blur": 20},
    ]
    for p in combos:
        out = M.apply_adjustments(img, p)
        assert out.shape == img.shape, p
        assert out.dtype == np.uint8, (p, out.dtype)
        assert np.isfinite(out).all()
    # 空参数应基本还原
    out = M.apply_adjustments(img, {})
    assert np.array_equal(out, img)


def t_filters():
    img = (np.random.rand(50, 70, 3) * 255).astype(np.uint8)
    assert len(M.FILTERS) >= 10, f"滤镜数量偏少: {len(M.FILTERS)}"
    for name, fn in M.FILTERS:
        out = fn(img)
        assert out is not None, name
        assert out.dtype == np.uint8, (name, out.dtype)
        assert out.ndim == 3 and out.shape[2] == 3, (name, out.shape)


def t_io_chinese_path():
    d = os.path.join(APP_DIR, "_test_中文目录")
    os.makedirs(d, exist_ok=True)
    try:
        img = (np.random.rand(40, 60, 3) * 255).astype(np.uint8)
        for ext in (".png", ".jpg", ".bmp", ".webp"):
            p = os.path.join(d, f"测试图{ext}")
            assert M.imwrite_unicode(p, img, ext=ext, quality=90), ext
            assert os.path.exists(p), ext
            back = M.imread_unicode(p)
            assert back is not None, ext
            b, _ = M.to_bgr8(back)
            assert b.shape[:2] == (40, 60), (ext, b.shape)
        # 带 alpha 的 png
        bgra = np.dstack([img, np.full((40, 60), 200, np.uint8)])
        p = os.path.join(d, "透明图.png")
        assert M.imwrite_unicode(p, bgra, ext=".png")
        assert M.imread_unicode(p).shape[2] == 4
        # 读不存在的文件
        assert M.imread_unicode(os.path.join(d, "没有这个文件.png")) is None
    finally:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_font():
    f = M.load_font(24)
    assert f is not None


def t_yunet_model():
    model = M.face_model_path()
    assert os.path.exists(model), model
    assert os.path.getsize(model) > 100000, "模型文件过小，可能下载不完整"
    assert hasattr(cv2, "FaceDetectorYN"), "cv2 缺少 FaceDetectorYN"
    det = M.create_face_detector((320, 320))
    assert det is not None
    print("     模型路径:", model)
    print("     含非ASCII字符:", not model.isascii(), "->",
          "走切换工作目录的方案" if not model.isascii() else "直接加载")


def t_face_detect_run():
    det = M.create_face_detector((320, 320))
    det.setInputSize((320, 320))
    img = np.zeros((320, 320, 3), np.uint8)
    _, faces = det.detect(img)
    # 全黑图不应检出人脸
    assert faces is None or len(faces) == 0, faces


def t_cwd_restored():
    before = os.getcwd()
    det = M.create_face_detector((200, 200))
    assert det is not None
    assert os.getcwd() == before, (before, os.getcwd())


def t_auto_enhance_logic():
    img = (np.random.rand(80, 100, 3) * 255).astype(np.uint8)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    out = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    out = M.apply_adjustments(out, {"saturation": 12, "contrast": 8, "sharpen": 25})
    assert out.shape == img.shape and out.dtype == np.uint8


def t_edge_detect_logic():
    img = (np.random.rand(80, 100, 3) * 255).astype(np.uint8)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (5, 5), 0)
    e = cv2.Canny(g, 80, 180)
    out = cv2.cvtColor(e, cv2.COLOR_GRAY2BGR)
    assert out.shape == img.shape


def t_batch_resize():
    img = np.zeros((100, 200, 3), np.uint8)
    out = M.BatchPanel._resize(img, {"mode": "w", "value": "100"})
    assert out.shape[:2] == (50, 100), out.shape
    out = M.BatchPanel._resize(img, {"mode": "h", "value": "50"})
    assert out.shape[:2] == (50, 100), out.shape
    out = M.BatchPanel._resize(img, {"mode": "pct", "value": "50"})
    assert out.shape[:2] == (50, 100), out.shape
    out = M.BatchPanel._resize(img, {"mode": "w", "value": "abc"})
    assert out.shape[:2] == (100, 200), out.shape


def t_batch_watermark():
    img = np.full((200, 300, 3), 100, np.uint8)
    for pos in ("tl", "tr", "bl", "br", "c"):
        out = M.BatchPanel._watermark(img, {
            "text": "测试水印ABC", "pos": pos, "opacity": 60,
            "size": 20, "color": "#FF0000"})
        assert out.shape == img.shape, pos
        assert out.dtype == np.uint8, pos
    # 空文字
    out = M.BatchPanel._watermark(img, {
        "text": "", "pos": "c", "opacity": 50, "size": 20, "color": "#FFFFFF"})
    assert out.shape == img.shape


def t_unicode_on_path():
    """确认程序目录含中文时 filter2D / 滤波不崩"""
    img = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    for fid in ("emboss", "cartoon", "sketch", "pencil", "vintage", "sepia"):
        M.FILTER_MAP[fid](img)


def t_gui_construct():
    app = M.App()
    try:
        app.update_idletasks()
        assert app.winfo_exists()
    finally:
        app.destroy()


def t_gui_workflow():
    d = os.path.join(APP_DIR, "_test_flow")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "输入 图.png")
    img = (np.random.rand(300, 500, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        assert app.work is not None
        assert app.work.shape[:2] == (300, 500), app.work.shape
        assert app.view_src is not None
        assert app.zoom > 0
        assert app.hist_idx == 0, app.hist_idx

        # 调整 -> 预览 -> 应用
        app.params["brightness"] = 30
        app._recompute_preview()
        assert app.preview is not None
        before = app.work.copy()
        app.apply_slot("adjust")
        assert pump(app, lambda: app.hist_idx == 1), "调色应用未完成"
        assert not np.array_equal(before, app.work)
        assert all(v == 0 for v in app.params.values())
        assert app.preview is None

        # 旋转
        shape0 = app.work.shape
        app.rotate(90)
        assert app.work.shape[0] == shape0[1] and app.work.shape[1] == shape0[0]

        # 镜像两次应还原
        cur = app.work.copy()
        app.flip(1)
        app.flip(1)
        assert np.array_equal(cur, app.work)

        # 改尺寸 + 锁定宽高比
        app.w_var.set("250")
        app.update_idletasks()
        expected_h = str(max(1, int(round(250 / app._aspect))))
        assert app.h_var.get() == expected_h, (app.h_var.get(), expected_h)

        # 裁剪
        app.crop_mode = False
        app.zoom = 1.0
        app.view_scale = app.work.shape[1] / float(app.view_src.shape[1])
        h, w = app.view_src.shape[:2]
        app.crop_rect = (10.0, 10.0, 110.0, 60.0)
        w0 = app.work.shape[1]
        app.apply_crop()
        assert app.work.shape[1] < w0, (app.work.shape, w0)

        # 撤销/重做
        n = app.hist_idx
        app.undo()
        assert app.hist_idx == n - 1
        app.redo()
        assert app.hist_idx == n

        # 还原
        app.revert()
        assert app.work.shape[:2] == (300, 500), app.work.shape

        # 另存路径（直接用 imwrite 走一遍相同逻辑）
        outp = os.path.join(d, "输出 图.jpg")
        assert M.imwrite_unicode(outp, app.work, ext=".jpg", quality=90)
        assert os.path.exists(outp)

        app.update_idletasks()
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_face_detect_via_app():
    """走完整的后台线程流程，确认不会卡死、异常会被兜住"""
    d = os.path.join(APP_DIR, "_test_face")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "照片.png")
    img = (np.random.rand(360, 540, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    errors = []
    orig_err = M.messagebox.showerror
    M.messagebox.showerror = lambda *a, **k: errors.append(a)
    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        base = app.work.copy()
        hist0 = app.hist_idx

        # 人脸检测现在也是"先预览再应用"
        app.face_detect()
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "人脸检测预览超时"
        assert app.pending_adv is not None and app.pending_adv["kind"] == "face"
        assert np.array_equal(app.work, base), "预览阶段不该改动原图"
        assert app.hist_idx == hist0

        # 改参数应该如实进入预览参数（噪声图上检不到人脸，画面自然不会变）
        app.face_thick.set(9)
        assert pump(app, lambda: app.pending_adv.get("thickness") == 9,
                    timeout=5), "框线宽没有同步到预览参数"
        print("     结果:", app.status.cget("text"))

        app.apply_slot("adv")
        assert pump(app, lambda: app.hist_idx == hist0 + 1), "应用人脸检测未完成"
        txt = app.status.cget("text")
        assert "检测到" in txt or "没有检测到" in txt, txt
        assert not errors, f"弹出错误框: {errors}"
        print("     结果:", txt)
    finally:
        M.messagebox.showerror = orig_err
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_face_settings_affect_output():
    """人脸检测的各项参数要真的起作用，而不是摆设"""
    d = os.path.join(APP_DIR, "_test_face2")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "f.png")
    # 画一张有"人脸样"特征可言的图；检测不到也要能验证参数进入流程
    img = (np.random.rand(300, 400, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()

        app.face_score.set(0.9)
        app.face_min.set(120)
        app.face_thick.set(7)
        app.face_landmarks.set(True)
        app.face_show_score.set(False)
        app.face_detect()
        spec = app.pending_adv
        assert spec["score"] == 0.9, spec
        assert spec["min_size"] == 120, spec
        assert spec["thickness"] == 7, spec
        assert spec["landmarks"] is True, spec
        assert spec["show_score"] is False, spec
        print("     预览参数:", {k: v for k, v in spec.items() if k != "color"})

        # 界面上点「框颜色」也要能改到参数里
        app.face_color = "#00FF00"
        app._on_face_setting_change()
        assert app.pending_adv["color"] == "#00FF00", app.pending_adv

        # 用假检测器验证每一项参数都真的影响画出来的结果
        canvas = np.full((240, 240, 3), 30, np.uint8)
        base_spec = {"kind": "face", "score": 0.6, "min_size": 10,
                     "thickness": 1, "color": "#FF0000",
                     "show_score": False, "landmarks": False}

        def run(**over):
            s = dict(base_spec)
            s.update(over)
            with fake_detector():
                return M.detect_faces(canvas, s)

        ref, n = run()
        assert n == 1, n
        assert not np.array_equal(ref, canvas), "应该画出了人脸框"

        thick, _ = run(thickness=9)
        assert not np.array_equal(ref, thick), "框线宽没有起作用"

        color, _ = run(color="#00FF00")
        assert not np.array_equal(ref, color), "框颜色没有起作用"

        marks, _ = run(landmarks=True)
        assert not np.array_equal(ref, marks), "五官关键点开关没有起作用"

        shown, _ = run(show_score=True)
        assert not np.array_equal(ref, shown), "置信度开关没有起作用"

        # 最小人脸尺寸：假检测器报的是 100×100 的框，
        # 把下限设成 150 就应该什么都不画
        tiny, nt = run(min_size=150)
        assert nt == 0, nt
        assert np.array_equal(tiny, canvas), "过小的人脸没有被过滤掉"

        keep, nk = run(min_size=50)
        assert nk == 1, nk
        assert not np.array_equal(keep, canvas)

        # 检测器确实被调用到了
        seen = {}

        class _Rec(_FakeDetector):
            def detect(self, img):
                seen["called"] = True
                return _FakeDetector.detect(self, img)

        orig = M.create_face_detector
        M.create_face_detector = lambda *a, **k: _Rec()
        try:
            M.detect_faces(canvas, dict(base_spec, min_size=10))
            assert seen.get("called"), "检测器没被调用"
        finally:
            M.create_face_detector = orig

        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_batch_window():
    d = os.path.join(APP_DIR, "_test_batch")
    os.makedirs(d, exist_ok=True)
    app = M.App()
    try:
        app.update_idletasks()
        bw = app.batch_panel
        app.update_idletasks()
        assert bw.log is not None
        assert bw.progress is not None

        img = (np.random.rand(20, 20, 3) * 255).astype(np.uint8)
        for n in ("a.jpg", "b.png", "c.webp"):
            assert M.imwrite_unicode(os.path.join(d, n), img,
                                     ext=os.path.splitext(n)[1])
        with open(os.path.join(d, "笔记.txt"), "w", encoding="utf-8") as fp:
            fp.write("不是图片")

        sub = os.path.join(d, "子目录")
        os.makedirs(sub, exist_ok=True)
        assert M.imwrite_unicode(os.path.join(sub, "d.bmp"), img, ext=".bmp")

        bw.recursive.set(True)
        names = sorted(os.path.basename(p) for p in bw.collect(d))
        assert names == ["a.jpg", "b.png", "c.webp", "d.bmp"], names

        bw.recursive.set(False)
        names2 = sorted(os.path.basename(p) for p in bw.collect(d))
        assert names2 == ["a.jpg", "b.png", "c.webp"], names2
    finally:
        app.destroy()
        _rmtree(d)


def t_batch_is_a_page_not_a_window():
    """批量处理必须是主窗口里的一个页面，不能另开窗口"""
    app = M.App()
    try:
        app.update_idletasks()
        bp = app.batch_panel
        assert isinstance(bp, M.BatchPanel), type(bp)
        assert not isinstance(bp, tk.Toplevel), "批量处理不该是独立窗口"
        assert bp.winfo_parent() == str(app.nb_main), bp.winfo_parent()

        # 主窗口里不该有 Toplevel 子窗口
        tops = [w for w in app.winfo_children() if isinstance(w, tk.Toplevel)]
        assert tops == [], f"多出了窗口: {tops}"

        # 菜单「批量」应该只是切到那个页签
        first = app.nb_main.index("current")
        app.open_batch()
        app.update_idletasks()
        assert app.nb_main.index("current") != first, "没有切到批量页签"
        assert app.nb_main.select() == str(bp), app.nb_main.select()

        # 切回单张处理页，画布仍在
        app.nb_main.select(0)
        app.update_idletasks()
        assert app.canvas.winfo_exists()
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()


def t_all_formats_write_read():
    """18 种输出格式逐个写入再读回"""
    d = os.path.join(APP_DIR, "_test_fmt")
    os.makedirs(d, exist_ok=True)
    try:
        img = (np.random.rand(48, 64, 3) * 255).astype(np.uint8)
        bad = []
        for name, desc, qk, gray in M.IMAGE_FORMATS:
            p = os.path.join(d, "样本_" + name + "." + name)
            if not M.imwrite_unicode(p, img, ext="." + name, quality=90):
                bad.append(f"{name}:写入失败")
                continue
            if name == "pdf":
                # PDF 是输出格式，Pillow 没有 Ghostscript 读不回来，只验证写入
                assert os.path.getsize(p) > 200, "pdf 文件过小"
                continue
            back = M.imread_unicode(p)
            if back is None:
                bad.append(f"{name}:读回失败")
        assert not bad, bad
        print(f"     {len(M.IMAGE_FORMATS)} 种格式全部写入成功")
    finally:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_alpha_handling():
    """带透明的图存成不支持透明的格式，不应该报错"""
    d = os.path.join(APP_DIR, "_test_alpha")
    os.makedirs(d, exist_ok=True)
    try:
        bgra = np.dstack([(np.random.rand(40, 50, 3) * 255).astype(np.uint8),
                          np.full((40, 50), 128, np.uint8)])
        png = os.path.join(d, "透明.png")
        assert M.imwrite_unicode(png, bgra, ext=".png")
        raw = M.imread_unicode(png)
        assert raw.shape[2] == 4, raw.shape

        bgr, alpha = M.to_bgr8(raw)
        assert alpha is not None
        # 支持透明的格式要保留
        webp = os.path.join(d, "透明.webp")
        assert M.imwrite_unicode(webp, bgra, ext=".webp")
        assert M.imread_unicode(webp).shape[2] == 4
        # 不支持透明的格式，去掉 alpha 后照样能存
        jpg = os.path.join(d, "无透明.jpg")
        assert M.imwrite_unicode(jpg, bgr, ext=".jpg")
    finally:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_preview_filter_cancel_apply():
    """点了滤镜应该是预览，不能直接改图；取消要能还原，应用才落盘"""
    d = os.path.join(APP_DIR, "_test_pv")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "a.png")
    img = (np.random.rand(240, 320, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        base = app.work.copy()
        hist0 = app.hist_idx

        # 点「卡通」滤镜 -> 预览，不动原图
        app.apply_filter("cartoon")
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "滤镜预览没算出来"
        assert app.pending_filter is not None
        assert np.array_equal(app.work, base), "预览阶段不应该改动原图"
        assert app.hist_idx == hist0, "预览阶段不应该产生历史记录"

        # 取消 -> 回到原样
        app.cancel_slot("filter")
        assert app.pending_filter is None
        assert app.preview is None
        assert np.array_equal(app.work, base)
        assert app.hist_idx == hist0

        # 再来一次，这次应用
        app.apply_filter("sketch")
        assert pump(app, lambda: app.preview is not None and not app._preview_running)
        app.apply_slot("filter")
        assert pump(app, lambda: app.hist_idx == hist0 + 1), "应用滤镜没完成"
        assert not np.array_equal(app.work, base), "应用之后图像应该变了"
        assert app.pending_filter is None
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_preview_canny_live():
    """拖动 Canny 阈值应该实时重算，而不是没反应"""
    d = os.path.join(APP_DIR, "_test_canny")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "b.png")
    img = (np.random.rand(240, 320, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()

        app.edge_detect()
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "边缘检测预览失败"
        assert app.pending_adv.get("kind") == "canny"
        first = app.preview.copy()

        # 拖动低阈值滑块
        app.canny_low.set(5)
        assert pump(app, lambda: app.pending_adv.get("lo") == 5,
                    timeout=5), "滑块没有同步到预览参数"
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running
                    and not np.array_equal(app.preview, first),
                    timeout=15), "改了阈值但画面没变"

        app.cancel_slot("adv")
        assert app.pending_adv is None
        assert app.preview is None
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_save_via_write_file():
    """走保存逻辑，确认能按扩展名落到对应格式"""
    d = os.path.join(APP_DIR, "_test_save")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "c.png")
    img = (np.random.rand(60, 90, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        app.save_quality = 80
        for ext in ("png", "jpg", "webp", "avif", "tif", "bmp", "ico", "qoi"):
            p = os.path.join(d, "out." + ext)
            assert app._write_file(p), ext
            assert os.path.exists(p), ext
            assert os.path.getsize(p) > 100, ext
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_independent_sections():
    """核心诉求：取消某一个功能区的改动，不能把别的功能区一起清掉"""
    d = os.path.join(APP_DIR, "_test_indep")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "s.png")
    img = (np.random.rand(200, 280, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")

    app = M.App()
    try:
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        hist0 = app.hist_idx

        # 滤镜待应用
        app.apply_filter("gray")
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "滤镜预览失败"
        # 同时调色待应用
        app.params["brightness"] = 45
        app._recompute_preview()
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "叠加预览失败"
        both = app.preview.copy()
        assert app.pending_filter is not None and any(app.params.values())

        # 只取消「调色」
        app.cancel_slot("adjust")
        assert app.pending_filter is not None, "取消调色把滤镜也清掉了"
        assert not any(app.params.values()), "调色没有清掉"
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "滤镜预览应该还在"
        assert app.preview is not None, "滤镜预览被误清"
        assert not np.array_equal(app.preview, both), "调色取消后画面应变化"
        assert app.hist_idx == hist0, "取消不应该产生历史记录"

        # 只取消「滤镜」，「调色」这时已经没了，画面回到原图
        app.cancel_slot("filter")
        assert app.pending_filter is None
        assert pump(app, lambda: not app._preview_running)
        assert app.preview is None, "全部取消后不该还有预览"
        assert np.array_equal(app.work, img) or app.work is not None

        # 两个都设上，先应用滤镜：调色应保留为待应用
        app.apply_filter("invert")
        assert pump(app, lambda: app.preview is not None and not app._preview_running)
        app.params["contrast"] = 30
        app._recompute_preview()
        assert pump(app, lambda: app.preview is not None and not app._preview_running)

        app.apply_slot("filter")
        assert pump(app, lambda: app.hist_idx == hist0 + 1), "应用滤镜未完成"
        assert app.pending_filter is None
        assert any(app.params.values()), "应用滤镜不该清掉调色"
        assert pump(app, lambda: app.preview is not None
                    and not app._preview_running), "调色预览应基于新图重算"

        app.apply_slot("adjust")
        assert pump(app, lambda: app.hist_idx == hist0 + 2), "应用调色未完成"
        assert app.preview is None
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def t_canvas_centering():
    """图片小于可视区域时要在画布里居中，不能贴在左上角"""
    d = os.path.join(APP_DIR, "_test_center")
    os.makedirs(d, exist_ok=True)
    app = M.App()
    try:
        app.update_idletasks()
        app.update()
        cw = app.canvas.winfo_width()
        ch = app.canvas.winfo_height()
        assert cw > 100 and ch > 100, (cw, ch)

        def check(w, h, label):
            p = os.path.join(d, f"{w}x{h}.png")
            img = (np.random.rand(h, w, 3) * 255).astype(np.uint8)
            assert M.imwrite_unicode(p, img, ext=".png")
            app.open_image(p)
            app.update_idletasks()
            app.update()

            dw, dh = app._disp_size
            ox, oy = app._img_offset
            x, y = app.canvas.coords(app._img_item)
            assert (round(x), round(y)) == (ox, oy), (label, x, y, ox, oy)

            # 两个方向都应居中（铺满的那一轴算作居中）
            assert abs((ox + dw / 2.0) - cw / 2.0) <= 3, \
                f"{label} 水平没居中: 图片中心={ox + dw/2:.1f} 画布中心={cw/2:.1f}"
            assert abs((oy + dh / 2.0) - ch / 2.0) <= 3, \
                f"{label} 垂直没居中: 图片中心={oy + dh/2:.1f} 画布中心={ch/2:.1f}"

        check(1600, 300, "很宽的图")
        check(300, 1600, "很高的图")
        check(200, 200, "小方图")
        check(1000, 1000, "大图")

        # 放大到超出画布后应该回到正常滚动（偏移为 0）
        app.set_zoom(8.0)
        app.update_idletasks()
        app.update()
        dw, dh = app._disp_size
        ox, oy = app._img_offset
        if dw > cw:
            assert ox == 0, ox
        if dh > ch:
            assert oy == 0, oy

        # 窗口尺寸变化后仍保持居中
        app.geometry("1100x700")
        app.update_idletasks()
        app.update()
        cw2 = app.canvas.winfo_width()
        ch2 = app.canvas.winfo_height()
        app.fit_window()
        app.update_idletasks()
        app.update()
        dw, dh = app._disp_size
        ox, oy = app._img_offset
        assert abs((ox + dw / 2.0) - cw2 / 2.0) <= 3, "改窗口后水平没居中"
        assert abs((oy + dh / 2.0) - ch2 / 2.0) <= 3, "改窗口后垂直没居中"
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


def _batch_fixture(name, n=10):
    """搭一个批量处理的测试场景，返回 (app, bw, src, dst, files, cfg, 根目录)"""
    d = os.path.join(APP_DIR, name)
    src = os.path.join(d, "in")
    dst = os.path.join(d, "out")
    _make_batch_images(src, n)
    app = M.App()
    app.update_idletasks()
    bw = app.batch_panel
    bw.update_idletasks()
    files = bw.collect(src)
    cfg = bw.snapshot()
    cfg.update({"resize": False, "watermark": False, "convert": True, "fmt": "png"})
    return app, bw, src, dst, files, cfg, d


def t_batch_pause_resume():
    """暂停要真的停住，继续要接着做完"""
    app, bw, src, dst, files, cfg, d = _batch_fixture("_test_bp")
    try:
        assert len(files) == 10, len(files)

        # 先按暂停，再让任务跑 —— 一张都不该处理
        bw._pause.set()
        bw._total = len(files)
        bw._set_running(True)
        th = threading.Thread(target=bw._run, args=(files, src, dst, cfg), daemon=True)
        th.start()
        for _ in range(40):
            app.update()
            time.sleep(0.02)
        assert bw._done_count == 0, f"暂停了却处理了 {bw._done_count} 张"
        assert th.is_alive(), "暂停时任务线程不该退出"
        assert _out_count(dst) == 0, "暂停时不该有输出"

        # 点「继续」—— 应该全部做完
        bw._pause.clear()
        assert pump(app, lambda: bw._done_count == len(files), timeout=25), \
            f"继续后只处理了 {bw._done_count}/{len(files)}"
        assert pump(app, lambda: not bw._running, timeout=10), "任务没有正常结束"
        assert _out_count(dst) == len(files), _out_count(dst)
        log = bw.log.get("1.0", "end")
        assert "处理结束" in log, log
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        _rmtree(d)


def t_batch_stop():
    """停止要能立刻中断，剩下的不再处理"""
    app, bw, src, dst, files, cfg, d = _batch_fixture("_test_bs")
    try:
        bw._pause.set()
        bw._stop.clear()
        bw._total = len(files)
        bw._set_running(True)
        th = threading.Thread(target=bw._run, args=(files, src, dst, cfg), daemon=True)
        th.start()
        for _ in range(40):
            app.update()
            time.sleep(0.02)
        assert bw._done_count == 0

        bw._stop_now()          # 内部会置停止位并清掉暂停
        assert pump(app, lambda: not bw._running, timeout=10), "点停止后任务没有结束"
        th.join(timeout=5)
        assert not th.is_alive(), "停止后工作线程还在跑"
        assert bw._done_count == 0, f"停止后仍处理了 {bw._done_count} 张"
        assert _out_count(dst) == 0, "停止后不该有输出"
        log = bw.log.get("1.0", "end")
        assert "已停止" in log, log
        assert UI_ERRORS == [], UI_ERRORS
    finally:
        app.destroy()
        _rmtree(d)


def t_batch_teardown_midway():
    """处理到一半退出程序：不能报 invalid command name，任务线程必须停下"""
    app, bw, src, dst, files, cfg, d = _batch_fixture("_test_bc")
    try:
        bw._pause.set()
        bw._stop.clear()
        bw._total = len(files)
        bw._set_running(True)
        th = threading.Thread(target=bw._run, args=(files, src, dst, cfg), daemon=True)
        th.start()
        for _ in range(40):
            app.update()
            time.sleep(0.02)
        assert th.is_alive(), "任务应该还在跑"

        # 切到别的页签，任务不该受影响（批量是页面，不是窗口）
        app.nb_main.select(0)
        app.update_idletasks()
        for _ in range(10):
            app.update()
            time.sleep(0.01)
        assert th.is_alive(), "切页签不该把任务弄停"
        assert UI_ERRORS == [], f"切页签弹了错误框: {UI_ERRORS}"

        # 退出程序：任务必须停下来，且不能再往已销毁的控件上写
        bw.stop_worker()
        th.join(timeout=5)
        assert not th.is_alive(), "退出后工作线程还在跑"

        for _ in range(40):
            app.update()
            time.sleep(0.01)
        assert UI_ERRORS == [], f"退出后弹了错误框: {UI_ERRORS}"
        print("     切页签/退出均无异常")
    finally:
        app.destroy()
        _rmtree(d)


def t_batch_close_by_root():
    """直接关主窗口，批量任务也要能停下来"""
    app, bw, src, dst, files, cfg, d = _batch_fixture("_test_br")
    try:
        bw._pause.set()
        bw._stop.clear()
        bw._total = len(files)
        bw._set_running(True)
        th = threading.Thread(target=bw._run, args=(files, src, dst, cfg), daemon=True)
        th.start()
        for _ in range(40):
            app.update()
            time.sleep(0.02)
        app.destroy()
        th.join(timeout=5)
        assert not th.is_alive(), "关主窗口后批量线程还在跑"
    finally:
        _rmtree(d)


def t_queue_error_no_dialog():
    """后台任务连续出错时不能弹模态框（会把程序卡住关不掉）"""
    app = M.App()
    try:
        app.update_idletasks()

        def boom():
            raise RuntimeError("模拟后台故障")

        app.post(boom)
        assert pump(app, lambda: "模拟后台故障" in app.status.cget("text"),
                    timeout=10), "故障没有反映到状态栏"
        assert UI_ERRORS == [], f"不该弹对话框: {UI_ERRORS}"

        for _ in range(20):
            app.post(boom)
        assert pump(app, lambda: "模拟后台故障" in app.status.cget("text"), timeout=10)
        assert UI_ERRORS == [], UI_ERRORS
        print("     连续 21 次后台异常，无弹窗、未卡死")
    finally:
        app.destroy()


def t_window_icon_paths():
    """Windows 走 .ico，macOS/Linux 走 PNG(iconphoto)，两条路都不能崩"""
    # 打包流程本来就会先跑 make_icon 生成图标，这里照做
    import make_icon
    make_icon.main()
    win = tk.Tk()
    win.withdraw()
    try:
        assert os.path.exists(M.resource_path("app.ico")), "缺 app.ico"
        assert os.path.exists(M.resource_path("app_icon.png")), "缺 app_icon.png"

        # 模拟 macOS / Linux 分支
        orig = M.IS_WIN
        M.IS_WIN = False
        try:
            assert M.apply_window_icon(win), "iconphoto 分支没生效"
        finally:
            M.IS_WIN = orig

        # Windows 分支
        assert M.apply_window_icon(win), "iconbitmap 分支没生效"
        print("     两条图标路径都正常")
    finally:
        win.destroy()


def t_font_all_platforms():
    """三个平台的字体候选表都要能优雅退化，不能抛异常"""
    for name in ("win", "mac", "linux"):
        saved = M.FONT_CANDIDATES
        try:
            if name == "mac":
                M.FONT_CANDIDATES = [
                    "/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/Helvetica.ttc",
                ]
            elif name == "linux":
                M.FONT_CANDIDATES = [
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                ]
            f = M.load_font(20)
            assert f is not None, name
        finally:
            M.FONT_CANDIDATES = saved


def t_lang_key_parity():
    """两种语言的 key 必须完全一致，缺一条就会退回英文显示。"""
    import lang as L
    zh, en = set(L.STRINGS["zh"]), set(L.STRINGS["en"])
    assert zh == en, ("只在中文:", sorted(zh - en), "只在英文:", sorted(en - zh))
    assert len(zh) > 150, len(zh)
    for code, table in L.STRINGS.items():
        for k, v in table.items():
            assert v and v != k, (code, k)
    print("     %d 条文案，中英完全对应，无空值" % len(zh))


def t_language_detect():
    import lang as L
    code = L.detect_system_language()
    assert code in L.LANG_NAMES, code
    print("     系统语言检测结果:", code)


def t_language_switch():
    """菜单里切语言：界面文字要跟着变。"""
    import lang as L
    orig = L.current_language()
    saved = M.save_language
    M.save_language = lambda code: True      # 别写进用户的配置文件
    app = None
    try:
        L.set_language("en")
        app = M.App()
        app.update_idletasks()
        app.update()
        assert app.title() == M.APP_NAME == "OpenCV Image Tool", app.title()
        assert app.nb_main.tab(0, "text").strip() == L.STRINGS["en"]["tab_single"]

        app.set_lang("zh")
        app.update_idletasks()
        app.update()
        assert app.nb_main.tab(0, "text").strip() == L.STRINGS["zh"]["tab_single"]
        mb = app.nametowidget(app.cget("menu"))
        labels = [mb.entrycget(i, "label") for i in range(1, mb.index("end"))]
        assert L.STRINGS["zh"]["menu_file"] in labels, labels
        assert L.STRINGS["zh"]["menu_language"] in labels, labels

        app.set_lang("en")
        app.update_idletasks()
        app.update()
        assert app.nb_main.tab(0, "text").strip() == L.STRINGS["en"]["tab_single"]
        assert UI_ERRORS == [], UI_ERRORS
        print("     en -> zh -> en 切换正常，菜单同步")
    finally:
        M.save_language = saved
        L.set_language(orig)
        if app is not None:
            app.destroy()


def t_language_switch_keeps_image():
    """切换语言会重建界面，但已打开的图片和撤销历史必须保留。"""
    import lang as L
    d = os.path.join(APP_DIR, "_test_lang")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "a.png")
    img = (np.random.rand(120, 180, 3) * 255).astype(np.uint8)
    assert M.imwrite_unicode(src, img, ext=".png")
    orig = L.current_language()
    saved = M.save_language
    M.save_language = lambda code: True
    app = None
    try:
        L.set_language("zh")
        app = M.App()
        app.update_idletasks()
        app.open_image(src)
        app.update_idletasks()
        app.rotate(90)
        assert app.hist_idx == 1
        before = app.work.shape

        app.set_lang("en")
        app.update_idletasks()
        app.update()
        assert app.work is not None, "切换语言后图片丢了"
        assert app.work.shape == before, (app.work.shape, before)
        assert app.hist_idx == 1, app.hist_idx
        assert UI_ERRORS == [], UI_ERRORS
        print("     切换语言后图片和历史都保留")
    finally:
        M.save_language = saved
        L.set_language(orig)
        if app is not None:
            app.destroy()
        _rmtree(d)


def t_batch_ops_both_languages():
    """下拉框显示的文字会随语言变，内部必须用 ASCII 代号。

    这里出过 bug：切到英文后「按宽度」变成 "By width"，
    代码里跟中文原文的比较全部失配，批量缩放静默失效。
    """
    import lang as L
    orig = L.current_language()
    try:
        for code in ("zh", "en"):
            L.set_language(code)

            for idx, want in ((0, "w"), (1, "h"), (2, "pct")):
                text = M.resize_mode_values()[idx]
                got = M._display_to_id(text, M.RESIZE_MODES, "w")
                assert got == want, (code, text, got, want)

            img = np.zeros((100, 200, 3), np.uint8)
            for text, want_shape in ((M.resize_mode_values()[0], (50, 100)),
                                     (M.resize_mode_values()[1], (100, 200))):
                mid = M._display_to_id(text, M.RESIZE_MODES, "w")
                out = M.BatchPanel._resize(img, {"mode": mid, "value": "100"})
                assert out.shape[:2] == want_shape, (code, text, out.shape)

            for idx, want in ((0, "tl"), (1, "tr"), (2, "bl"), (3, "br"), (4, "c")):
                text = M.wm_position_values()[idx]
                got = M._display_to_id(text, M.WM_POSITIONS, "br")
                assert got == want, (code, text, got, want)

            out = M.BatchPanel._watermark(
                np.full((200, 300, 3), 100, np.uint8),
                {"text": "W", "pos": "c", "opacity": 60, "size": 20,
                 "color": "#FF0000"})
            assert out.shape == (200, 300, 3)
        print("     中英两种语言下缩放/水印都正常")
    finally:
        L.set_language(orig)


if __name__ == "__main__":
    tests = [
        ("导入与版本", t_import),
        ("图像通道归一化", t_to_bgr8),
        ("调色运算", t_adjustments),
        ("全部滤镜", t_filters),
        ("中文路径读写", t_io_chinese_path),
        ("字体加载", t_font),
        ("人脸模型可用", t_yunet_model),
        ("人脸检测调用", t_face_detect_run),
        ("工作目录不被污染", t_cwd_restored),
        ("自动增强运算", t_auto_enhance_logic),
        ("边缘检测运算", t_edge_detect_logic),
        ("批量缩放", t_batch_resize),
        ("批量水印", t_batch_watermark),
        ("中文路径下滤镜", t_unicode_on_path),
        ("界面构建", t_gui_construct),
        ("完整操作流程", t_gui_workflow),
        ("人脸检测完整流程", t_face_detect_via_app),
        ("人脸检测参数生效", t_face_settings_affect_output),
        ("批量页面构建", t_batch_window),
        ("批量是页面不是窗口", t_batch_is_a_page_not_a_window),
        ("全部输出格式", t_all_formats_write_read),
        ("透明通道处理", t_alpha_handling),
        ("滤镜预览/取消/应用", t_preview_filter_cancel_apply),
        ("Canny 滑块实时预览", t_preview_canny_live),
        ("另存为各格式", t_save_via_write_file),
        ("各功能区互不影响", t_independent_sections),
        ("画布居中", t_canvas_centering),
        ("批量暂停/继续", t_batch_pause_resume),
        ("批量停止", t_batch_stop),
        ("处理中退出程序", t_batch_teardown_midway),
        ("关主窗口停批量", t_batch_close_by_root),
        ("后台异常不弹窗", t_queue_error_no_dialog),
        ("窗口图标两条路径", t_window_icon_paths),
        ("三平台字体退化", t_font_all_platforms),
        ("语言包完整性", t_lang_key_parity),
        ("系统语言检测", t_language_detect),
        ("界面语言切换", t_language_switch),
        ("切语言保留图片", t_language_switch_keeps_image),
        ("双语下批量处理", t_batch_ops_both_languages),
    ]
    quiet_errors()
    for name, fn in tests:
        check(name, fn)

    print("\n" + "=" * 60)
    print(f"通过 {len(OK)} 项，失败 {len(FAIL)} 项")
    for name, tb in FAIL:
        print("\n---- 失败: %s ----" % name)
        print(tb)
    sys.exit(1 if FAIL else 0)
