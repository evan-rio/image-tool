# -*- coding: utf-8 -*-
"""生成程序图标 app.ico

画一个"照片"图标：蓝绿渐变圆角底 + 白色相纸 + 太阳 + 两座山。
需要改配色或样式时改这里的常量，然后重新运行本脚本。
"""

import os
import numpy as np
from PIL import Image, ImageDraw

S = 512                      # 先按大尺寸画，再缩成各个尺寸存进 ico
TOP = (45, 120, 255)         # 背景渐变：上
BOTTOM = (24, 194, 156)      # 背景渐变：下
PAPER = (255, 255, 255, 255)
SCREEN = (226, 240, 255, 255)
SUN = (255, 196, 60, 255)
HILL_FAR = (90, 170, 120, 255)
HILL_NEAR = (52, 132, 96, 255)

ICON_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def gradient_bg(size):
    y = np.linspace(0.0, 1.0, size)[:, None]
    top = np.array(TOP, dtype=np.float32)
    bot = np.array(BOTTOM, dtype=np.float32)
    row = top[None, :] * (1 - y) + bot[None, :] * y          # (size, 3)
    grid = np.repeat(row[:, None, :], size, axis=1)          # (size, size, 3)
    return Image.fromarray(grid.astype(np.uint8), "RGB")


def build():
    img = gradient_bg(S).convert("RGBA")

    # 圆角遮罩
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=255)
    img.putalpha(mask)

    d = ImageDraw.Draw(img)

    # 相纸
    m = int(S * 0.18)
    off = int(S * 0.05)          # 相纸上沿留白比下沿少，像拍立得
    paper = [m, m + off, S - m, S - m - off * 2]
    d.rounded_rectangle(paper, radius=int(S * 0.06), fill=PAPER)

    # 相纸里的画面
    p = int(S * 0.045)
    x0, y0 = paper[0] + p, paper[1] + p
    x1, y1 = paper[2] - p, paper[3] - p
    d.rectangle([x0, y0, x1, y1], fill=SCREEN)

    w, h = x1 - x0, y1 - y0

    # 太阳
    r = int(S * 0.042)
    cx = x1 - int(w * 0.26)
    cy = y0 + int(h * 0.24)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN)

    # 远山、近山
    d.polygon([(x0, y1),
               (x0 + int(w * 0.34), y0 + int(h * 0.38)),
               (x0 + int(w * 0.70), y1)], fill=HILL_FAR)
    d.polygon([(x0 + int(w * 0.38), y1),
               (x0 + int(w * 0.68), y0 + int(h * 0.50)),
               (x1, y1)], fill=HILL_NEAR)

    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = build()

    # Windows 用 .ico（内含多个尺寸）
    ico = os.path.join(here, "app.ico")
    img.save(ico, format="ICO", sizes=ICON_SIZES)
    print("已生成:", ico, os.path.getsize(ico), "字节")

    # macOS 用 .icns（Dock / Finder 图标）
    icns = os.path.join(here, "app.icns")
    try:
        # Pillow 直接写，尺寸由 macOS 自己挑
        img.save(icns, format="ICNS")
        print("已生成:", icns, os.path.getsize(icns), "字节")
    except Exception as e:
        print("写 .icns 失败:", e)

    # 窗口图标用的 PNG（macOS / Linux 的 iconphoto 需要）
    png = os.path.join(here, "app_icon.png")
    img.resize((256, 256), Image.LANCZOS).save(png, format="PNG")
    print("已生成:", png, os.path.getsize(png), "字节")


if __name__ == "__main__":
    main()
