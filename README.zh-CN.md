# OpenCV 图片处理

[English](README.md) | **简体中文**

一个**全程离线**的桌面图片处理软件，支持 Windows 与 macOS（Apple Silicon 与 Intel）。不需要安装 Python，下载即用。所有处理都在你自己的电脑上完成：**不联网、不上传任何图片**。

## 下载

到 **[Releases](../../releases/latest)** 页面下载最新版：

| 平台 | 文件 |
|---|---|
| **Windows** | `…-windows-setup.exe`（安装包）或 `…-windows-portable.zip` |
| **macOS（M 系列）** | `…-macos-arm64.dmg` |
| **macOS（Intel）** | `…-macos-x86_64.dmg` |

macOS 版另有 `.zip` 压缩包可选。

**首次打开** —— 程序没有商业代码签名，系统会拦一次。Windows：点「**更多信息**」→「**仍要运行**」；macOS：在图标上**右键 → 打开**，弹窗里再点一次「**打开**」。

## 功能

### 单张处理

| 分区 | 内容 |
|---|---|
| **调色** | 亮度、对比度、饱和度、色调、锐化、模糊 —— 拖动滑块**即时预览** |
| **滤镜** | 灰度、黑白、反色、怀旧褐色、复古、素描、铅笔画、卡通、浮雕、暖色调、冷色调、油画、细节增强、色调分离、颗粒、去雾 |
| **增强** | 降噪、锐化细节、局部对比度（CLAHE）、暗角 —— 拖动**即时预览** |
| **几何** | 旋转（90° / 180° / 任意角度）、镜像、修改尺寸（可锁定比例）、鼠标框选裁剪、四点**透视矫正** |
| **高级** | 自动增强、边缘检测（Canny 阈值实时可调）、人脸检测（灵敏度、最小人脸、框颜色、线宽、置信度、五官关键点均可调） |

### 批量处理

对整个文件夹批量做**缩放 / 滤镜 / 画质增强 / 转格式 / 加水印**，可叠加，结果输出到单独文件夹、**不改动原图**。支持暂停、继续、停止。

### 其他

- **中英双语界面** —— 自动跟随系统语言，也可在「语言」菜单里随时切换，选择会被记住
- 每个功能区**各自独立的「应用 / 重置」**，互不影响
- 撤销 / 重做（上限 20 步），「按住看原图」随时对比
- 图片在画布中自动居中显示
- **macOS 触控板** —— 双指滚动平移、捏合缩放；按住 **Command** 滚动同样可缩放
- **完整支持中文路径**的读取与保存

### 支持的输出格式（18 种）

`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`

## 系统要求

Windows 10 / 11（64 位）· macOS 11 或更高 · 不需要单独安装 Python

## 免责声明

本软件按**「原样」**提供，不附带任何担保，使用风险自负，作者不对使用它产生的任何损失或损害负责。

**请先备份原图。** 缩放、有损格式转换、裁剪等操作**可能造成不可逆的画质损失**，不要在唯一的原件上直接操作。

人脸检测、边缘检测基于统计模型，可能漏检、误检，**不可用于安全、身份核验、医疗、法律等严肃场景**。

请合法使用，并确保对所处理的图片拥有合法权利。本软件**不包含任何联网功能**，不采集、不上传、不存储任何数据。与 OpenCV.org 官方无关。

## 从源码构建

> PyInstaller 不支持交叉编译：生成 macOS 版需要一台 Mac（或使用云端构建）。

macOS 本机构建：

```bash
chmod +x build_mac.sh
./build_mac.sh arm64      # M 系列芯片
./build_mac.sh x86_64     # Intel 芯片
```

云端构建（不需要有 Mac）—— 工作流存放在 `packaging` 分支，在 `macos-14` 机器上运行，Intel 版在 Rosetta 2 下产出，不需要 Intel 机器：

```bash
gh workflow run build-macos.yml --ref packaging
gh workflow run build-macos.yml --ref packaging -f publish=true   # 同时发布 Release
```

发布标签自动取自 `main.py` 里的 `APP_VERSION`，所以标签、文件名和程序版本号永远不会对不上；产物由构建机直接推到 Release，不经过本地磁盘。

自检：

```bash
pip install -r requirements.txt
python selftest.py
```

## 第三方组件

| 组件 | 用途 | 许可 |
|---|---|---|
| [OpenCV](https://opencv.org/) | 图像处理核心 | Apache License 2.0 |
| [NumPy](https://numpy.org/) | 数组运算 | BSD 3-Clause |
| [Pillow](https://python-pillow.org/) | 图像编解码（AVIF / ICO / PDF / TGA / QOI） | MIT-CMU |
| [Python](https://www.python.org/) | 运行时 | PSF License |
| [YuNet 人脸检测模型](https://github.com/opencv/opencv_zoo) | 人脸检测 | Apache License 2.0 |

OpenCV 通过 PyPI 安装（`opencv-python`），本仓库不内嵌、也不改动它的源码。OpenCV 自身还内含 libjpeg-turbo、libpng、libtiff、libwebp、FFmpeg 等第三方库，其许可文本见官方发行包的 `etc/licenses`。官方地址：[opencv/opencv](https://github.com/opencv/opencv) · [发行版](https://github.com/opencv/opencv/releases) · [opencv_zoo](https://github.com/opencv/opencv_zoo)。

## 开源许可

MIT License，详见 [LICENSE](LICENSE)。
