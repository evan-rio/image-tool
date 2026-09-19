# OpenCV 图片处理

[English](README.md) | **简体中文**

一个**全程离线**的桌面图片处理软件，带图形界面。支持 Windows 与 macOS（Apple Silicon 与 Intel）。

不需要安装 Python，下载即用。所有处理都在你自己的电脑上完成：**不联网、不上传任何图片**。

---

## 下载

到 **[Releases](../../releases/latest)** 页面下载：

| 平台 | 文件 | 说明 |
|---|---|---|
| **Windows** | `image-tool-1.0.9-windows-setup.exe` | 安装包，创建开始菜单和桌面快捷方式 |
| **Windows** | `image-tool-1.0.9-windows-portable.zip` | 便携版，解压即用，免安装 |
| **macOS（M 系列）** | `image-tool-1.0.9-macos-arm64.dmg` | 打开后把图标拖进「应用程序」 |
| **macOS（Intel）** | `image-tool-1.0.9-macos-x86_64.dmg` | 同上，适用于 Intel 芯片的 Mac |

macOS 版另有 `.zip` 压缩包可选。

### 首次打开

本项目没有购买商业代码签名证书，第一次打开时系统会拦一下：

- **Windows**：SmartScreen 提示「Windows 已保护你的电脑」→ 点「**更多信息**」→「**仍要运行**」
- **macOS**：提示「无法验证开发者」→ 在图标上**右键 → 打开** → 弹窗里再点一次「**打开**」

只需操作一次，之后正常双击即可。

---

## 功能

### 单张处理

| 分区 | 内容 |
|---|---|
| **调色** | 亮度、对比度、饱和度、色调、锐化、模糊 —— 拖动滑块**即时预览** |
| **滤镜** | 灰度、黑白、反色、怀旧褐色、复古、素描、铅笔画、卡通、浮雕、暖色调、冷色调、油画、细节增强、色调分离、颗粒、去雾 |
| **增强** | 降噪、锐化细节、局部对比度（CLAHE）、暗角 —— 拖动**即时预览** |
| **几何** | 旋转（90° / 180° / 任意角度）、水平与垂直镜像、修改尺寸（可锁定比例）、鼠标拖拽框选裁剪、四点**透视矫正** |
| **高级** | 自动增强、边缘检测（Canny 阈值实时可调）、人脸检测（灵敏度、最小人脸、框颜色、线宽、置信度、五官关键点均可调） |

### 批量处理

对整个文件夹批量做**缩放 / 滤镜 / 画质增强 / 转格式 / 加水印**，可叠加，结果输出到单独文件夹、**不改动原图**。支持**暂停、继续、停止**。

### 其他

- **中英双语界面** —— 自动跟随系统语言，也可在「语言」菜单里随时切换，选择会被记住
- 每个功能区**各自独立的「应用 / 重置」**，互不影响
- 撤销 / 重做（上限 20 步）
- 「按住看原图」随时对比
- 图片在画布中自动居中显示
- **macOS 触控板** —— 双指滚动平移图片、捏合缩放；按住 **Command** 滚动同样可缩放
- **完整支持中文路径**的读取与保存

### 支持的输出格式（18 种）

`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`

---

## 系统要求

| 平台 | 要求 |
|---|---|
| Windows | Windows 10 / 11（64 位） |
| macOS | macOS 11 或更高 |

不需要单独安装 Python，程序自带运行时。

---

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

---

## 从源码构建

> **PyInstaller 不支持交叉编译。** 在 Windows 或 Linux 上无法生成 macOS 版 —— 需要一台 Mac，或使用下面的云端构建。

### macOS 本机构建

```bash
chmod +x build_mac.sh
./build_mac.sh arm64      # M 系列芯片
./build_mac.sh x86_64     # Intel 芯片
```

### 云端构建（不需要有 Mac）

`build` 分支存放 GitHub Actions 工作流，在 `macos-14`（Apple Silicon）机器上同时构建两个架构 —— Intel 版通过安装 python.org 的 universal2 版 Python 并在 Rosetta 2 下运行来产出，**不需要 Intel 机器，也不用排队等 `macos-13`**。

```bash
# 只构建
gh workflow run build-macos.yml --ref build

# 构建并发布 GitHub Release
gh workflow run build-macos.yml --ref build -f publish=true
```

带上 `publish=true` 时，构建机会把 `.dmg` 和 `.zip` **直接推到 Release**，不经过任何人的本地磁盘。发布标签自动取自 `main.py` 里的 `APP_VERSION`，所以标签、文件名和程序版本号永远不会对不上。

### 运行自检

`selftest.py` 是开发期自检脚本，覆盖调色、滤镜、格式读写、人脸检测参数、批量任务控制、画布居中、多线程安全等 34 项：

```bash
pip install -r requirements.txt
python selftest.py
```

---

## 第三方组件

| 组件 | 用途 | 许可 |
|---|---|---|
| [OpenCV](https://opencv.org/) | 图像处理核心 | Apache License 2.0 |
| [NumPy](https://numpy.org/) | 数组运算 | BSD 3-Clause |
| [Pillow](https://python-pillow.org/) | 图像编解码（AVIF / ICO / PDF / TGA / QOI） | MIT-CMU |
| [Python](https://www.python.org/) | 运行时 | PSF License |
| [YuNet 人脸检测模型](https://github.com/opencv/opencv_zoo) | 人脸检测 | Apache License 2.0 |

OpenCV 自身还内含多个第三方库（libjpeg-turbo、libpng、libtiff、libwebp、FFmpeg 等），各自的许可文本见 OpenCV 官方发行包的 `etc/licenses` 目录。

### OpenCV 是从哪来的

**本仓库不内嵌 OpenCV 的源码**，也没有任何本地改动过的 OpenCV 副本。构建时通过 PyPI 安装 `opencv-python`，直接使用官方为各平台编译好的二进制包 —— 和其他所有用 OpenCV 的项目做法一致。

这样做的好处是：仓库体积小、克隆快，而且用到的 OpenCV 永远对应一个已发布的官方版本。需要看源码的话，在这里：

| 项目 | 官方地址 |
|---|---|
| OpenCV 库 | [github.com/opencv/opencv](https://github.com/opencv/opencv) |
| OpenCV 发行版 | [github.com/opencv/opencv/releases](https://github.com/opencv/opencv/releases) |
| 模型仓库（YuNet 等） | [github.com/opencv/opencv_zoo](https://github.com/opencv/opencv_zoo) |

如果你想**改这个软件本身的行为**，整个程序就是 `main.py` 一个文件 —— 见 [从源码构建](#从源码构建)。整个过程完全不涉及 OpenCV 源码。

---

## 开源许可

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

你被允许自由使用、修改、分发本项目的源代码，条件是保留版权声明。源码同样**不提供任何担保**。

---

## 目录说明

```
main.py            软件本体（全部功能都在这一个文件里）
make_icon.py       生成图标：app.icns（macOS）/ app.ico（Windows）/ app_icon.png
selftest.py        开发期自检脚本（34 项）
build_mac.sh       macOS 本机打包脚本
requirements.txt   依赖清单
LICENSE            MIT 许可
models/            人脸检测模型
README.md          英文说明
README.zh-CN.md    中文说明（本文件）
```

> 构建用的 GitHub Actions 工作流存放在 `build` 分支，不放在源码分支。
