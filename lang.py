# -*- coding: utf-8 -*-
"""多语言支持。

软件名固定为 "OpenCV Image Tool"，两种语言下都一样 —— 名字是品牌，
只有界面文字分语言。

加一种新语言只需要两步：
  1. 在 LANG_NAMES 里加一行（代码 → 该语言自己的写法）
  2. 在 STRINGS 里加一整块字典（照抄 "en" 那份，把值翻译掉）

程序启动时自动跟随系统语言；用户在「语言」菜单里手动选过之后，
选择会被记住（存一个小配置文件），不再跟随系统。
"""

import os
import sys
import json

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# 软件名：不随语言变化
APP_NAME = "OpenCV Image Tool"

# 代码 -> 菜单里显示的名字（用该语言自己的写法，这是惯例）
LANG_NAMES = {
    "zh": "简体中文",
    "en": "English",
}

DEFAULT_LANG = "en"

STRINGS = {
    # ==================================================================
    # 简体中文
    # ==================================================================
    "zh": {
        # ---- 输出格式说明 ----
        "fmt_jpg": "JPEG  最常用，体积小，有损",
        "fmt_png": "PNG   无损，支持透明",
        "fmt_webp": "WebP  体积比 JPEG 更小，现代格式",
        "fmt_avif": "AVIF  体积最小，画质好（编码较慢）",
        "fmt_bmp": "BMP   无压缩位图",
        "fmt_tif": "TIFF  印刷与专业领域常用",
        "fmt_jp2": "JPEG 2000  高压缩比",
        "fmt_gif": "GIF   静态单帧",
        "fmt_ico": "ICO   Windows 图标",
        "fmt_pdf": "PDF   单页文档",
        "fmt_tga": "TGA   Targa",
        "fmt_qoi": "QOI   无损、编码极快",
        "fmt_hdr": "HDR   高动态范围",
        "fmt_ppm": "PPM   无损中间格式",
        "fmt_pgm": "PGM   灰度图",
        "fmt_pbm": "PBM   黑白位图",
        "fmt_pfm": "PFM   浮点图",
        "fmt_ras": "RAS   Sun Raster",

        # ---- 滤镜名 ----
        "filter_gray": "灰度",
        "filter_bw": "黑白(二值)",
        "filter_invert": "反色",
        "filter_sepia": "怀旧褐色",
        "filter_vintage": "复古",
        "filter_sketch": "素描",
        "filter_pencil": "铅笔画",
        "filter_cartoon": "卡通",
        "filter_emboss": "浮雕",
        "filter_warm": "暖色调",
        "filter_cool": "冷色调",
        "filter_oil": "油画",
        "filter_detail": "细节增强",
        "filter_posterize": "色调分离",
        "filter_grain": "颗粒",
        "filter_dehaze": "去雾",

        # ---- 工具名（状态栏用）----
        "tool_filter": "滤镜",
        "tool_auto": "自动增强",
        "tool_face": "人脸检测",
        "tool_canny": "边缘检测 {lo}/{hi}",
        "tool_preview": "预览",
        "tool_enhance": "画质增强",

        # ---- 菜单 ----
        "menu_file": "文件",
        "menu_open": "打开图片…",
        "menu_save": "保存",
        "menu_save_as": "另存为…",
        "menu_save_quality": "保存质量…",
        "menu_exit": "退出",
        "menu_edit": "编辑",
        "menu_undo": "撤销",
        "menu_redo": "重做",
        "menu_revert": "还原到打开时的状态",
        "menu_image": "图像",
        "menu_rot_ccw": "向左旋转 90°",
        "menu_rot_cw": "向右旋转 90°",
        "menu_rot_180": "旋转 180°",
        "menu_flip_h": "水平镜像",
        "menu_flip_v": "垂直镜像",
        "menu_advanced": "高级",
        "menu_auto_enhance": "自动增强",
        "menu_edge": "边缘检测",
        "menu_face": "人脸检测",
        "menu_batch": "批量",
        "menu_batch_open": "批量处理文件夹…",
        "menu_language": "语言",
        "menu_help": "帮助",
        "menu_help_usage": "使用说明",
        "menu_about": "关于",

        # ---- 工具栏 ----
        "tb_open": "打开",
        "tb_save": "保存",
        "tb_save_as": "另存为",
        "tb_undo": "撤销",
        "tb_redo": "重做",
        "tb_fit": "适应窗口",
        "tb_zoom_reset": "1:1",
        "tb_zoom_in": "放大",
        "tb_zoom_out": "缩小",
        "tb_crop": "裁剪模式",
        "tb_crop_exit": "退出裁剪",
        "tb_crop_apply": "应用裁剪",
        "tb_compare": "按住看原图",

        # ---- 主页面 ----
        "tab_single": "单张处理",
        "tab_batch": "批量处理",
        "status_batch_hint": "批量处理：选好文件夹和处理项后点「开始处理」",
        "status_ready": "就绪 — 请先打开一张图片",

        # ---- 调色 ----
        "tab_adjust": "调色",
        "adj_brightness": "亮度",
        "adj_contrast": "对比度",
        "adj_saturation": "饱和度",
        "adj_warmth": "色调",
        "adj_sharpen": "锐化",
        "adj_blur": "模糊",
        "adj_apply": "应用调色",
        "adj_hint": "拖动滑块即时预览，满意后点「应用调色」。",
        "adj_nothing": "没有需要应用的调色",
        "adj_applied": "调色已应用",

        # ---- 滤镜 ----
        "tab_filter": "滤镜",
        "filter_hint": "点一下即可预览，不会立刻改动原图。",
        "filter_apply": "应用滤镜",

        # ---- 增强 ----
        "tab_enhance": "增强",
        "enh_sec_clean": "降噪与锐化",
        "enh_sec_tone": "对比与氛围",
        "enh_denoise": "降噪",
        "enh_sharpen": "锐化细节",
        "enh_clahe": "局部对比度",
        "enh_vignette": "暗角",
        "enh_apply": "应用增强",
        "enh_nothing": "四个参数都是 0，没有可应用的效果。",
        "enh_hint": "拖动滑块实时预览，点「应用增强」才会写入图片。",

        # ---- 几何 ----
        "tab_geometry": "几何",
        "geo_hint": "这里的操作点一下立刻生效，\n不满意点「撤销上一步」或按 Ctrl+Z。",
        "geo_undo": "撤销上一步",
        "geo_rotate": "旋转",
        "geo_rot_ccw": "↺ 90°",
        "geo_rot_cw": "↻ 90°",
        "geo_rot_180": "180°",
        "geo_flip_h": "水平镜像",
        "geo_flip_v": "垂直镜像",
        "geo_rotate_free": "任意角度旋转",
        "geo_apply_rotate": "旋转",
        "geo_resize": "修改尺寸",
        "geo_w": "宽",
        "geo_h": "高",
        "geo_lock": "锁定宽高比",
        "geo_apply_resize": "应用尺寸",
        "geo_crop": "裁剪",
        "geo_crop_hint": "点「裁剪模式」后在图上拖拽框选，\n再点「应用裁剪」。",
        "geo_clear_sel": "清除选区",
        "geo_persp": "透视矫正",
        "geo_persp_exit": "退出透视模式",
        "geo_persp_hint": "点「透视矫正」后在图上依次点选四个角点，\n再点「应用透视」把画面拉正。",
        "geo_persp_apply": "应用透视",
        "geo_persp_clear": "清除四点",
        "geo_persp_clicked": "已选 {n}/4 个点",
        "geo_persp_need4": "请先点选四个角点。",
        "geo_persp_degenerate": "四个点太接近、共线或面积过小，请重新点选。",
        "geo_persp_done": "透视矫正完成（{w}×{h}）",

        # ---- 高级 ----
        "tab_advanced": "高级",
        "adv_group": "自动增强 / 边缘检测",
        "adv_auto": "自动增强（对比度+色彩）",
        "adv_canny": "边缘检测（Canny）",
        "adv_canny_th": "Canny 阈值",
        "adv_low": "低阈值  {v}",
        "adv_high": "高阈值  {v}",
        "adv_apply": "应用处理",
        "face_group": "人脸检测",
        "face_sensitivity": "灵敏度",
        "face_min": "最小人脸",
        "face_unit_px": "像素",
        "face_thick": "框线宽",
        "face_color": "框颜色",
        "face_show_score": "显示置信度数值",
        "face_landmarks": "标出五官关键点",
        "face_preview": "预览人脸检测",
        "face_hint": "调好参数点这里预览，满意后点下面的「应用处理」。",

        # ---- 通用按钮 / 状态 ----
        "btn_reset": "重置",
        "previewing": "正在预览…",
        "reset_done": "已重置本页设置",
        "applying": "正在应用：{label}…",
        "applied": "已应用：{label}",

        # ---- 打开 / 保存 ----
        "dlg_choose_image": "选择图片",
        "ft_images": "图片文件",
        "ft_all": "所有文件",
        "err_empty_image": "图片内容为空或格式不支持。",
        "err_open_image": "无法打开图片：\n{path}",
        "opened": "已打开：{path}",
        "untitled": "未命名.jpg",
        "saved": "已保存：{path}",
        "save_failed": "保存失败。\n\n可能是该格式无法保存当前图像（比如把带透明的图存成 {fmt}）。",
        "dlg_quality": "保存质量",
        "quality_hint": "有损格式（JPEG / WebP / AVIF / JPEG 2000）的保存质量：\n数值越大越清晰，文件也越大（1-100，当前 {q}）",
        "quality_set": "保存质量已设为 {q}",

        # ---- 状态栏 ----
        "status_size": "尺寸 {w}×{h}   通道 {c}",
        "status_zoom": "缩放 {z}%   原图 {w}×{h}",

        # ---- 历史 ----
        "hist_earliest": "已经是最早的状态了",
        "hist_no_redo": "没有可重做的操作",
        "reverted": "已还原到打开时的状态",

        # ---- 几何操作提示 ----
        "rotated": "旋转 {a}°",
        "flipped": "镜像",
        "resized": "尺寸改为 {w}×{h}",
        "cropped": "裁剪为 {w}×{h}",
        "err_size_num": "宽高必须是数字",
        "err_size_pos": "宽高必须大于 0",

        # ---- 裁剪 ----
        "crop_hint_click": "在图片上按住左键拖拽框选区域",
        "crop_exited": "已退出裁剪模式",
        "crop_need_sel": "请先在裁剪模式下框选区域",
        "crop_too_small": "选区太小了",
        "crop_selected": "已框选 {w}×{h} 像素，点「应用裁剪」",

        # ---- 人脸检测 ----
        "face_no_model": "找不到人脸检测模型文件：\n{path}",
        "face_detected": "检测到 {n} 张人脸",
        "face_none": "没有检测到人脸",

        # ---- 关于 / 帮助 ----
        "about": "{name}  v{ver}\n\n基于 OpenCV {cv} 与 Python 构建\n本机离线运行，不联网、不上传任何图片。",
        "help": (
            "1. 「打开」选择一张图片，滚轮缩放，按住左键拖动可平移。\n"
            "2. 左侧「调色」拖动滑块实时预览，满意后点「应用调色」。\n"
            "3. 「几何」可旋转、镜像、改尺寸；点「裁剪模式」后在图上拖拽框选，再点「应用裁剪」。\n"
            "4. 「高级」里有一键自动增强、边缘检测、人脸检测。\n"
            "5. 「批量」可对整个文件夹做缩放 / 转格式 / 加水印。\n"
            "6. Ctrl+Z 撤销，Ctrl+Y 重做，Ctrl+S 保存。"
        ),

        # ---- 批量处理 ----
        "batch_title": "批量处理",
        "batch_desc": "对一整个文件夹的图片批量做缩放 / 转格式 / 加水印。三种处理可以叠加，结果输出到单独的文件夹，不改动原图。",
        "grp_folders": "文件夹",
        "lbl_src": "源文件夹",
        "lbl_dst": "输出到",
        "btn_browse": "浏览…",
        "chk_recursive": "包含子文件夹（输出目录会被自动跳过）",
        "grp_ops": "要做的处理（可多选）",
        "chk_resize": "缩放",
        "mode_w": "按宽度",
        "mode_h": "按高度",
        "mode_pct": "按百分比",
        "unit_px_pct": "像素 / %",
        "chk_convert": "转格式",
        "lbl_quality": "质量",
        "chk_watermark": "加水印",
        "wm_default": "© 我的水印",
        "lbl_pos": "位置",
        "pos_tl": "左上角",
        "pos_tr": "右上角",
        "pos_bl": "左下角",
        "pos_br": "右下角",
        "pos_c": "居中",
        "lbl_font_size": "字号",
        "lbl_opacity": "透明度",
        "btn_color": "颜色",
        "grp_task": "任务",
        "btn_start": "开始处理",
        "btn_pause": "暂停",
        "btn_resume": "继续",
        "btn_stop": "停止",
        "grp_log": "处理记录",
        "state_ready": "就绪",
        "state_paused": "已暂停",
        "state_running": "处理中 {done}/{total}",
        "log_start": "开始处理，共 {n} 张",
        "log_resume": "▶ 继续处理",
        "log_paused": "⏸ 已暂停（点「继续」接着做）",
        "log_stopping": "■ 正在停止……当前这张做完就停",
        "log_ok": "[{i}/{n}] 完成：{name}",
        "log_fail": "[{i}/{n}] 失败：{name} — {err}",
        "log_stopped": "—— 已停止：成功 {ok} 张，失败 {fail} 张 ——",
        "log_finished": "—— 处理结束：成功 {ok} 张，失败 {fail} 张 ——",
        "done_title": "批量处理",
        "done_msg": "处理完成\n成功 {ok} 张，失败 {fail} 张",
        "dlg_choose_src": "选择源文件夹",
        "dlg_choose_dst": "选择输出文件夹",
        "warn_no_src": "请选择有效的源文件夹",
        "info_no_images": "该文件夹里没有找到图片",
        "err_makedirs": "无法创建输出文件夹：\n{err}",
        "confirm_start": "共找到 {n} 张图片，开始处理？",
        "err_read": "无法读取",
        "err_write": "写入失败",
        "quit_batch_title": "批量处理",
        "quit_batch_msg": "批量处理还在进行中，确定要退出吗？\n\n已经处理完的图片会保留，剩下的不再处理。",

        # ---- 语言 ----
        "lang_switched": "语言已切换为「{name}」",
        "err_fail": "操作失败：\n{err}",
        "lang_busy": "批量处理正在进行中，请等它结束再切换语言。",
    },

    # ==================================================================
    # English
    # ==================================================================
    "en": {
        "fmt_jpg": "JPEG  most common, small files, lossy",
        "fmt_png": "PNG   lossless, supports transparency",
        "fmt_webp": "WebP  smaller than JPEG, modern format",
        "fmt_avif": "AVIF  smallest files, good quality (slow to encode)",
        "fmt_bmp": "BMP   uncompressed bitmap",
        "fmt_tif": "TIFF  common in print and professional work",
        "fmt_jp2": "JPEG 2000  high compression ratio",
        "fmt_gif": "GIF   static, single frame",
        "fmt_ico": "ICO   Windows icon",
        "fmt_pdf": "PDF   single-page document",
        "fmt_tga": "TGA   Targa",
        "fmt_qoi": "QOI   lossless, extremely fast to encode",
        "fmt_hdr": "HDR   high dynamic range",
        "fmt_ppm": "PPM   lossless intermediate format",
        "fmt_pgm": "PGM   greyscale image",
        "fmt_pbm": "PBM   black and white bitmap",
        "fmt_pfm": "PFM   floating-point image",
        "fmt_ras": "RAS   Sun Raster",

        "filter_gray": "Greyscale",
        "filter_bw": "Black & white",
        "filter_invert": "Invert",
        "filter_sepia": "Sepia",
        "filter_vintage": "Vintage",
        "filter_sketch": "Sketch",
        "filter_pencil": "Pencil",
        "filter_cartoon": "Cartoon",
        "filter_emboss": "Emboss",
        "filter_warm": "Warm",
        "filter_cool": "Cool",
        "filter_oil": "Oil paint",
        "filter_detail": "Detail enhance",
        "filter_posterize": "Posterize",
        "filter_grain": "Film grain",
        "filter_dehaze": "Dehaze",

        "tool_filter": "Filter",
        "tool_auto": "Auto enhance",
        "tool_face": "Face detection",
        "tool_canny": "Edge detection {lo}/{hi}",
        "tool_preview": "Preview",
        "tool_enhance": "Image enhance",

        "menu_file": "File",
        "menu_open": "Open image…",
        "menu_save": "Save",
        "menu_save_as": "Save as…",
        "menu_save_quality": "Save quality…",
        "menu_exit": "Exit",
        "menu_edit": "Edit",
        "menu_undo": "Undo",
        "menu_redo": "Redo",
        "menu_revert": "Revert to opened state",
        "menu_image": "Image",
        "menu_rot_ccw": "Rotate 90° left",
        "menu_rot_cw": "Rotate 90° right",
        "menu_rot_180": "Rotate 180°",
        "menu_flip_h": "Flip horizontally",
        "menu_flip_v": "Flip vertically",
        "menu_advanced": "Advanced",
        "menu_auto_enhance": "Auto enhance",
        "menu_edge": "Edge detection",
        "menu_face": "Face detection",
        "menu_batch": "Batch",
        "menu_batch_open": "Process a folder…",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_help_usage": "How to use",
        "menu_about": "About",

        "tb_open": "Open",
        "tb_save": "Save",
        "tb_save_as": "Save as",
        "tb_undo": "Undo",
        "tb_redo": "Redo",
        "tb_fit": "Fit",
        "tb_zoom_reset": "1:1",
        "tb_zoom_in": "Zoom in",
        "tb_zoom_out": "Zoom out",
        "tb_crop": "Crop mode",
        "tb_crop_exit": "Exit crop",
        "tb_crop_apply": "Apply crop",
        "tb_compare": "Hold to compare",

        "tab_single": "Single image",
        "tab_batch": "Batch",
        "status_batch_hint": "Batch: choose your folders and options, then click Start",
        "status_ready": "Ready — open an image to begin",

        "tab_adjust": "Adjust",
        "adj_brightness": "Brightness",
        "adj_contrast": "Contrast",
        "adj_saturation": "Saturation",
        "adj_warmth": "Warmth",
        "adj_sharpen": "Sharpen",
        "adj_blur": "Blur",
        "adj_apply": "Apply",
        "adj_hint": "Drag the sliders for a live preview, then click Apply.",
        "adj_nothing": "Nothing to apply",
        "adj_applied": "Adjustments applied",

        "tab_filter": "Filters",
        "filter_hint": "Click a filter to preview it — your image is not changed yet.",
        "filter_apply": "Apply filter",

        "tab_enhance": "Enhance",
        "enh_sec_clean": "Denoise & sharpen",
        "enh_sec_tone": "Contrast & mood",
        "enh_denoise": "Denoise",
        "enh_sharpen": "Sharpen / detail",
        "enh_clahe": "Local contrast",
        "enh_vignette": "Vignette",
        "enh_apply": "Apply enhance",
        "enh_nothing": "All four values are 0 — nothing to apply.",
        "enh_hint": "Drag a slider to preview; click Apply to write the changes into the image.",

        "tab_geometry": "Geometry",
        "geo_hint": "These take effect immediately.\nIf you don't like the result, use Undo or Ctrl+Z.",
        "geo_undo": "Undo last step",
        "geo_rotate": "Rotate",
        "geo_rot_ccw": "↺ 90°",
        "geo_rot_cw": "↻ 90°",
        "geo_rot_180": "180°",
        "geo_flip_h": "Flip horizontally",
        "geo_flip_v": "Flip vertically",
        "geo_rotate_free": "Rotate by angle",
        "geo_apply_rotate": "Rotate",
        "geo_resize": "Resize",
        "geo_w": "W",
        "geo_h": "H",
        "geo_lock": "Keep aspect ratio",
        "geo_apply_resize": "Apply size",
        "geo_crop": "Crop",
        "geo_crop_hint": "Turn on Crop mode, drag on the image to select\nan area, then click Apply crop.",
        "geo_clear_sel": "Clear selection",
        "geo_persp": "Perspective",
        "geo_persp_exit": "Exit perspective",
        "geo_persp_hint": "Turn on Perspective, click the four corners on the image,\nthen click Apply perspective.",
        "geo_persp_apply": "Apply perspective",
        "geo_persp_clear": "Clear points",
        "geo_persp_clicked": "{n}/4 points selected",
        "geo_persp_need4": "Select four corners first.",
        "geo_persp_degenerate": "The four points are too close, collinear, or cover too small an area.",
        "geo_persp_done": "Perspective corrected ({w}×{h})",

        "tab_advanced": "Advanced",
        "adv_group": "Auto enhance / Edge detection",
        "adv_auto": "Auto enhance (contrast + colour)",
        "adv_canny": "Edge detection (Canny)",
        "adv_canny_th": "Canny thresholds",
        "adv_low": "Low  {v}",
        "adv_high": "High  {v}",
        "adv_apply": "Apply",
        "face_group": "Face detection",
        "face_sensitivity": "Sensitivity",
        "face_min": "Min face",
        "face_unit_px": "px",
        "face_thick": "Box width",
        "face_color": "Box colour",
        "face_show_score": "Show confidence",
        "face_landmarks": "Mark facial landmarks",
        "face_preview": "Preview face detection",
        "face_hint": "Adjust the settings, preview here, then click Apply below.",

        "btn_reset": "Reset",
        "previewing": "Previewing…",
        "reset_done": "Settings on this page reset",
        "applying": "Applying {label}…",
        "applied": "Applied: {label}",

        "dlg_choose_image": "Choose an image",
        "ft_images": "Image files",
        "ft_all": "All files",
        "err_empty_image": "The image is empty or its format is not supported.",
        "err_open_image": "Could not open the image:\n{path}",
        "opened": "Opened: {path}",
        "untitled": "untitled.jpg",
        "saved": "Saved: {path}",
        "save_failed": "Save failed.\n\nThis format may not be able to store the current image (for example, saving an image with transparency as {fmt}).",
        "dlg_quality": "Save quality",
        "quality_hint": "Save quality for lossy formats (JPEG / WebP / AVIF / JPEG 2000).\nHigher is clearer and larger (1-100, currently {q})",
        "quality_set": "Save quality set to {q}",

        "status_size": "Size {w}×{h}   Channels {c}",
        "status_zoom": "Zoom {z}%   Original {w}×{h}",

        "hist_earliest": "Already at the earliest state",
        "hist_no_redo": "Nothing to redo",
        "reverted": "Reverted to the opened state",

        "rotated": "Rotated {a}°",
        "flipped": "Flipped",
        "resized": "Resized to {w}×{h}",
        "cropped": "Cropped to {w}×{h}",
        "err_size_num": "Width and height must be numbers",
        "err_size_pos": "Width and height must be greater than 0",

        "crop_hint_click": "Hold the left mouse button and drag to select an area",
        "crop_exited": "Crop mode off",
        "crop_need_sel": "Select an area in crop mode first",
        "crop_too_small": "That selection is too small",
        "crop_selected": "Selected {w}×{h} px — click Apply crop",

        "face_no_model": "Face detection model not found:\n{path}",
        "face_detected": "Found {n} face(s)",
        "face_none": "No faces detected",

        "about": "{name}  v{ver}\n\nBuilt with OpenCV {cv} and Python\nRuns entirely offline — no network access, no uploads.",
        "help": (
            "1. Click Open to choose an image. Scroll to zoom, drag to pan.\n"
            "2. Drag the sliders in Adjust for a live preview, then click Apply.\n"
            "3. Geometry rotates, flips and resizes; turn on Crop mode, drag on\n"
            "   the image to select an area, then click Apply crop.\n"
            "4. Advanced has one-click auto enhance, edge detection and face detection.\n"
            "5. Batch resizes, converts and watermarks a whole folder.\n"
            "6. Ctrl+Z undo, Ctrl+Y redo, Ctrl+S save."
        ),

        "batch_title": "Batch processing",
        "batch_desc": "Resize, convert and watermark every image in a folder. The three operations stack, results go to a separate folder, and your originals are never modified.",
        "grp_folders": "Folders",
        "lbl_src": "Source",
        "lbl_dst": "Output to",
        "btn_browse": "Browse…",
        "chk_recursive": "Include subfolders (the output folder is skipped)",
        "grp_ops": "Operations (choose any combination)",
        "chk_resize": "Resize",
        "mode_w": "By width",
        "mode_h": "By height",
        "mode_pct": "By percent",
        "unit_px_pct": "px / %",
        "chk_convert": "Convert format",
        "lbl_quality": "Quality",
        "chk_watermark": "Watermark",
        "wm_default": "© my watermark",
        "lbl_pos": "Position",
        "pos_tl": "Top left",
        "pos_tr": "Top right",
        "pos_bl": "Bottom left",
        "pos_br": "Bottom right",
        "pos_c": "Centre",
        "lbl_font_size": "Size",
        "lbl_opacity": "Opacity",
        "btn_color": "Colour",
        "grp_task": "Task",
        "btn_start": "Start",
        "btn_pause": "Pause",
        "btn_resume": "Resume",
        "btn_stop": "Stop",
        "grp_log": "Log",
        "state_ready": "Ready",
        "state_paused": "Paused",
        "state_running": "Working {done}/{total}",
        "log_start": "Starting — {n} image(s)",
        "log_resume": "▶ Resumed",
        "log_paused": "⏸ Paused (click Resume to continue)",
        "log_stopping": "■ Stopping… finishing the current image",
        "log_ok": "[{i}/{n}] done: {name}",
        "log_fail": "[{i}/{n}] failed: {name} — {err}",
        "log_stopped": "—— Stopped: {ok} succeeded, {fail} failed ——",
        "log_finished": "—— Finished: {ok} succeeded, {fail} failed ——",
        "done_title": "Batch processing",
        "done_msg": "Finished\n{ok} succeeded, {fail} failed",
        "dlg_choose_src": "Choose the source folder",
        "dlg_choose_dst": "Choose the output folder",
        "warn_no_src": "Please choose a valid source folder",
        "info_no_images": "No images found in that folder",
        "err_makedirs": "Could not create the output folder:\n{err}",
        "confirm_start": "Found {n} image(s). Start processing?",
        "err_read": "could not read",
        "err_write": "could not write",
        "quit_batch_title": "Batch processing",
        "quit_batch_msg": "A batch is still running. Quit anyway?\n\nImages already processed are kept; the rest are skipped.",

        "lang_switched": "Language switched to {name}",
        "err_fail": "Something went wrong:\n{err}",
        "lang_busy": "A batch is still running. Please wait for it to finish before switching language.",
    },
}


# --------------------------------------------------------------------------
# 当前语言
# --------------------------------------------------------------------------

_current = DEFAULT_LANG


def available_languages():
    """[(代码, 显示名), ...]，按 LANG_NAMES 的顺序"""
    return list(LANG_NAMES.items())


def current_language():
    return _current


def set_language(code):
    global _current
    _current = code if code in STRINGS else DEFAULT_LANG
    return _current


def t(key, **kw):
    """取当前语言的文案；缺失时退回英文，再缺就返回 key 本身。"""
    table = STRINGS.get(_current) or STRINGS[DEFAULT_LANG]
    s = table.get(key)
    if s is None:
        s = STRINGS[DEFAULT_LANG].get(key, key)
    if kw:
        try:
            s = s.format(**kw)
        except Exception:
            pass
    return s


# --------------------------------------------------------------------------
# 跟随系统语言
# --------------------------------------------------------------------------

def _zh_from_env():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var)
        if v and v.lower().replace("-", "_").startswith("zh"):
            return True
    return False


def detect_system_language():
    """猜系统语言。目前只区分「中文」和「其他」，其他一律英文。"""
    try:
        if _zh_from_env():
            return "zh"

        if IS_WIN:
            import ctypes
            # GetUserDefaultUILanguage 返回的语言 ID，低 10 位是主语言，
            # 0x04 就是 LANG_CHINESE（简体繁体都算）
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if (langid & 0x3FF) == 0x04:
                return "zh"

        if IS_MAC:
            import subprocess
            out = subprocess.run(
                ["defaults", "read", "-g", "AppleLanguages"],
                capture_output=True, text=True, timeout=4).stdout
            if "zh" in out.lower():
                return "zh"
    except Exception:
        pass
    return DEFAULT_LANG


# --------------------------------------------------------------------------
# 记住用户的手动选择
# --------------------------------------------------------------------------

def config_path():
    if IS_WIN:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif IS_MAC:
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "image-tool", "settings.json")


def load_saved_language():
    """读用户手动选过的语言；没选过返回 None。"""
    try:
        with open(config_path(), "r", encoding="utf-8") as fp:
            code = json.load(fp).get("language")
        return code if code in STRINGS else None
    except Exception:
        return None


def save_language(code):
    """记住用户的选择。失败也只是下次不记住，不影响使用。"""
    try:
        p = config_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = {}
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as fp:
                    data = json.load(fp) or {}
            except Exception:
                data = {}
        data["language"] = code
        with open(p, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def init_language():
    """启动时调用：优先用用户手动选过的，否则跟随系统。"""
    code = load_saved_language() or detect_system_language()
    return set_language(code)
