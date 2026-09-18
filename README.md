# OpenCV Image Tool

A fully **offline** desktop image editor with a graphical interface. Available for Windows and macOS (Apple Silicon & Intel).

No Python installation required — download and run. All processing happens on your own machine: **no network access, no uploads, ever**.

> 中文说明见下方 [中文文档](#中文文档)。

---

## Download

Get the latest build from the **[Releases](../../releases/latest)** page:

| Platform | File | Notes |
|---|---|---|
| **Windows** | `image-tool-1.0.5-windows-setup.exe` | Installer — adds Start Menu and desktop shortcuts |
| **Windows** | `image-tool-1.0.5-windows-portable.zip` | Portable — unzip and run, no installation |
| **macOS (Apple Silicon)** | `image-tool-1.0.5-macos-arm64.dmg` | Open the DMG and drag the app to Applications |
| **macOS (Intel)** | `image-tool-1.0.5-macos-x86_64.dmg` | Same, for Intel-based Macs |

The macOS builds are also available as `.zip` archives if you prefer.

### First launch

This project is not signed with a commercial code-signing certificate, so the OS will warn you the first time:

- **Windows**: SmartScreen says *"Windows protected your PC"* → click **More info** → **Run anyway**
- **macOS**: *"cannot be opened because the developer cannot be verified"* → **right-click the icon → Open** → click **Open** again in the dialog

You only need to do this once.

---

## Features

### Single image

| Panel | Contents |
|---|---|
| **Adjust** | Brightness, contrast, saturation, warmth, sharpen, blur — live preview while dragging |
| **Filters** | Grayscale, black & white, invert, sepia, vintage, sketch, pencil, cartoon, emboss, warm, cool |
| **Geometry** | Rotate (90° / 180° / any angle), flip horizontal & vertical, resize (aspect-ratio lock), drag-to-crop |
| **Advanced** | Auto-enhance, edge detection (live Canny thresholds), face detection (sensitivity, minimum face size, box colour, line width, confidence labels, facial landmarks) |

### Batch processing

Resize, convert format, and watermark an entire folder. The three operations stack, results go to a separate output folder, and **your originals are never modified**. Supports **pause, resume, and stop**.

### Other

- Each panel has its **own Apply / Reset** — changes in one panel never affect another
- Undo / redo (20 steps)
- Hold **"View original"** to compare at any time
- Images are automatically centred on the canvas
- **Full support for non-ASCII (e.g. Chinese) file paths**

### Supported output formats (18)

`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`

---

## System requirements

| Platform | Requirement |
|---|---|
| Windows | Windows 10 / 11 (64-bit) |
| macOS | macOS 11 or later |

No separate Python installation is needed — the runtime is bundled.

---

## ⚠️ Disclaimer

**Please read before use. Downloading or using this software means you understand and accept all of the following.**

### 1. No warranty

This software is provided **"AS IS"**, without warranty of any kind, express or implied, including but not limited to the warranties of **merchantability, fitness for a particular purpose, accuracy, and non-infringement**. The software may contain defects, bugs, or unexpected behaviour. The author does not guarantee that it will meet any particular requirement, or that its operation will be uninterrupted or error-free.

### 2. Use at your own risk

**You assume full responsibility for all consequences of using this software.** To the maximum extent permitted by law, the author and contributors **shall not be liable for any loss or damage**, including but not limited to:

- Corrupted images, loss of image quality, or lost metadata
- Files overwritten, accidentally deleted, or unrecoverable
- Data loss, device failure, or business interruption
- Any direct, indirect, incidental, special, punitive, or consequential damages

> **⚠️ Back up your original images before processing.**
> Image operations — especially resizing, lossy format conversion, and cropping — **may cause irreversible quality loss**. Always keep a copy of the original; never work directly on your only copy.

### 3. Detection results are indicative only

Face detection and edge detection are based on statistical models and **are not guaranteed to be accurate or complete**. They may miss faces, produce false positives, or show bias. These results **do not constitute professional judgement** and must not be used for security, identity verification, medical, or legal purposes.

### 4. Lawful use

**You agree not to use this software for any unlawful purpose**, including but not limited to:

- Collecting, processing, or recognising other people's facial images or biometric data without their consent
- Infringing on anyone's portrait rights, privacy, reputation, or intellectual property
- Creating or distributing illegal content
- Any act that violates the laws or regulations of your jurisdiction

**You are responsible for ensuring you hold the legal rights to any image you process**, and you bear full legal responsibility for any infringement or violation.

### 5. Not affiliated with OpenCV

This software uses the OpenCV library, but has **no affiliation, sponsorship, or endorsement relationship with OpenCV.org**. It is an independent third-party work, not an official product. The OpenCV name and trademarks belong to their respective owners.

### 6. Third-party components

This software bundles several third-party open-source components (see [Third-party components](#third-party-components)). These are provided under **their own original licences**, may carry additional terms, and **likewise come with no warranty**. You must comply with those licences when using this software.

### 7. Privacy

This software contains **no networking functionality whatsoever**. It does not collect, upload, or store any of your images or usage data. All processing happens in local memory, and results are written only to the files and folders you specify.

---

## Building from source

> **PyInstaller does not support cross-compilation.** You cannot produce a macOS build on Windows or Linux — you need macOS, or use the cloud build below.

### macOS (local)

```bash
chmod +x build_mac.sh
./build_mac.sh arm64      # Apple Silicon
./build_mac.sh x86_64     # Intel
```

### Cloud build (no Mac required)

The `build` branch contains the GitHub Actions workflow. It builds both architectures on `macos-14` runners — the Intel build is produced by running an x86_64 Python under Rosetta 2 on an Apple Silicon runner.

```bash
gh workflow run build-macos.yml --ref build
gh run watch
```

### Running the self-test

`selftest.py` is a 34-case development test suite covering colour adjustment, filters, format I/O, face-detection parameters, batch task control, canvas centring, and thread safety:

```bash
pip install -r requirements.txt
python selftest.py
```

---

## Third-party components

| Component | Purpose | Licence |
|---|---|---|
| [OpenCV](https://opencv.org/) | Core image processing | Apache License 2.0 |
| [NumPy](https://numpy.org/) | Array operations | BSD 3-Clause |
| [Pillow](https://python-pillow.org/) | Image codecs (AVIF / ICO / PDF / TGA / QOI) | MIT-CMU |
| [Python](https://www.python.org/) | Runtime | PSF License |
| [YuNet face detection model](https://github.com/opencv/opencv_zoo) | Face detection | Apache License 2.0 |

OpenCV itself bundles further third-party libraries (libjpeg-turbo, libpng, libtiff, libwebp, FFmpeg, and others). Their licence texts are in the `etc/licenses` directory of the official OpenCV distribution.

---

## Licence

Released under the **MIT License** — see [LICENSE](LICENSE).

You are free to use, modify, and distribute the source code, provided the copyright notice is retained. The source is likewise provided **without any warranty**.

---
---

# 中文文档

一个**全程离线**的桌面图片处理软件，带图形界面。支持 Windows 与 macOS（Apple Silicon 与 Intel）。

不需要安装 Python，下载即用。所有处理都在你自己的电脑上完成：**不联网、不上传任何图片**。

## 下载

到 **[Releases](../../releases/latest)** 页面下载：

| 平台 | 文件 | 说明 |
|---|---|---|
| **Windows** | `image-tool-1.0.5-windows-setup.exe` | 安装包，创建开始菜单和桌面快捷方式 |
| **Windows** | `image-tool-1.0.5-windows-portable.zip` | 便携版，解压即用，免安装 |
| **macOS（M 系列）** | `image-tool-1.0.5-macos-arm64.dmg` | 打开后把图标拖进「应用程序」 |
| **macOS（Intel）** | `image-tool-1.0.5-macos-x86_64.dmg` | 同上，适用于 Intel 芯片的 Mac |

macOS 版另有 `.zip` 压缩包可选。

### 首次打开

本项目没有购买商业代码签名证书，第一次打开时系统会拦一下：

- **Windows**：SmartScreen 提示「Windows 已保护你的电脑」→ 点「**更多信息**」→「**仍要运行**」
- **macOS**：提示「无法验证开发者」→ 在图标上**右键 → 打开** → 弹窗里再点一次「**打开**」

只需操作一次，之后正常双击即可。

## 功能

### 单张处理

| 分区 | 内容 |
|---|---|
| **调色** | 亮度、对比度、饱和度、色调、锐化、模糊 —— 拖动滑块**即时预览** |
| **滤镜** | 灰度、黑白、反色、怀旧褐色、复古、素描、铅笔画、卡通、浮雕、暖色调、冷色调 |
| **几何** | 旋转（90° / 180° / 任意角度）、水平与垂直镜像、修改尺寸（可锁定比例）、鼠标拖拽框选裁剪 |
| **高级** | 自动增强、边缘检测（Canny 阈值实时可调）、人脸检测（灵敏度、最小人脸、框颜色、线宽、置信度、五官关键点均可调） |

### 批量处理

对整个文件夹批量做**缩放 / 转格式 / 加水印**，三种可叠加，结果输出到单独文件夹、**不改动原图**。支持**暂停、继续、停止**。

### 其他

- 每个功能区**各自独立的「应用 / 重置」**，互不影响
- 撤销 / 重做（上限 20 步）
- 「按住看原图」随时对比
- 图片在画布中自动居中显示
- **完整支持中文路径**的读取与保存

### 支持的输出格式（18 种）

`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`

## 系统要求

| 平台 | 要求 |
|---|---|
| Windows | Windows 10 / 11（64 位） |
| macOS | macOS 11 或更高 |

不需要单独安装 Python，程序自带运行时。

## ⚠️ 免责声明

**使用本软件前请务必阅读。下载或使用即表示你已理解并接受以下全部内容。**

### 1. 无担保

本软件按 **「原样」** 提供，不附带任何明示或暗示的担保，包括但不限于对**适销性、特定用途适用性、准确性、不侵权**的担保。软件可能存在缺陷、错误或未预料的行为，作者不保证它能满足你的任何特定需求，也不保证使用过程中不会出现中断或错误。

### 2. 使用风险自负

**你对使用本软件的一切后果自行承担全部责任。** 在法律允许的最大范围内，作者及贡献者**不对任何损失或损害承担责任**，包括但不限于：

- 图片损坏、画质损失、元数据丢失
- 文件被覆盖、误删或不可恢复
- 数据丢失、设备故障、业务中断
- 任何直接、间接、偶然、特殊、惩罚性或后果性的损害

> **⚠️ 强烈建议：处理前先备份原始图片。**
> 图片处理（尤其是缩放、有损格式转换、裁剪）**可能造成不可逆的画质损失**。请务必保留原图副本，不要在唯一的原件上直接操作。

### 3. 识别结果仅供参考

人脸检测、边缘检测等功能基于统计模型，**不保证结果的准确性或完整性**，可能漏检、误检或产生偏差。这些结果**不构成任何专业判断依据**，不可用于安全、身份核验、医疗、法律等严肃场景。

### 4. 合法使用

**你承诺不将本软件用于任何违法违规用途**，包括但不限于：

- 未经他人同意，采集、处理、识别他人人脸图像或生物特征信息
- 侵犯他人的肖像权、隐私权、名誉权或知识产权
- 制作、传播违法违规内容
- 任何违反你所在国家或地区法律法规的行为

**你应自行确保对所处理的图片拥有合法权利**，并自行承担因侵权或违规产生的全部法律责任。

### 5. 与 OpenCV 官方无关

本软件使用了 OpenCV 库，但**与 OpenCV 官方（OpenCV.org）没有任何隶属、赞助或背书关系**，是第三方独立作品，并非官方产品。OpenCV 的名称与商标归其各自所有者所有。

### 6. 第三方组件

本软件打包时包含了若干第三方开源组件（见上方 [第三方组件](#第三方组件)）。这些组件按其**各自的原许可**提供，可能附带额外条款，且**同样不提供任何担保**。使用本软件时你应一并遵守这些许可。

### 7. 隐私

本软件**不包含任何联网功能**，不采集、不上传、不存储你的任何图片或使用数据。所有处理均在本机内存中完成，处理结果只写入你自己指定的文件和文件夹。

## 从源码构建

> **PyInstaller 不支持交叉编译。** 在 Windows 或 Linux 上无法生成 macOS 版 —— 需要一台 Mac，或使用下面的云端构建。

### macOS 本机构建

```bash
chmod +x build_mac.sh
./build_mac.sh arm64      # M 系列芯片
./build_mac.sh x86_64     # Intel 芯片
```

### 云端构建（不需要有 Mac）

`build` 分支存放 GitHub Actions 工作流，在 `macos-14`（Apple Silicon）机器上同时构建两个架构 —— Intel 版通过 Rosetta 2 运行 x86_64 Python 交叉产出，不需要 Intel 机器。

```bash
gh workflow run build-macos.yml --ref build
gh run watch
```

### 运行自检

`selftest.py` 是开发期自检脚本，覆盖调色、滤镜、格式读写、人脸检测参数、批量任务控制、画布居中、多线程安全等 34 项：

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

OpenCV 自身还内含多个第三方库（libjpeg-turbo、libpng、libtiff、libwebp、FFmpeg 等），各自的许可文本见 OpenCV 官方发行包的 `etc/licenses` 目录。

## 开源许可

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

你被允许自由使用、修改、分发本项目的源代码，条件是保留版权声明。源码同样**不提供任何担保**。

## 目录说明

```
main.py            软件本体（全部功能都在这一个文件里）
make_icon.py       生成图标：app.icns（macOS）/ app.ico（Windows）/ app_icon.png
selftest.py        开发期自检脚本（34 项）
build_mac.sh       macOS 本机打包脚本
requirements.txt   依赖清单
LICENSE            MIT 许可
models/            人脸检测模型
```

> 构建用的 GitHub Actions 工作流存放在 `build` 分支，不放在源码分支。
