## Download

| Platform | File | Notes |
|---|---|---|
| **Windows** | `image-tool-1.0.7-windows-setup.exe` | Installer — adds Start Menu and desktop shortcuts |
| **Windows** | `image-tool-1.0.7-windows-portable.zip` | Portable — unzip and run, no installation |
| **macOS (Apple Silicon)** | `image-tool-1.0.7-macos-arm64.dmg` | Open the DMG and drag the app to Applications |
| **macOS (Intel)** | `image-tool-1.0.7-macos-x86_64.dmg` | For Intel-based Macs |

The macOS builds are also available as `.zip` archives. The bundled runtime means **no Python installation is required**.

## First launch

This project is not signed with a commercial code-signing certificate, so the OS will warn you the first time:

- **Windows**: SmartScreen says *"Windows protected your PC"* → click **More info** → **Run anyway**
- **macOS**: *"cannot be opened because the developer cannot be verified"* → **right-click the icon → Open** → click **Open** again in the dialog

You only need to do this once.

## What's in it

**Single image**
- **Adjust** — brightness, contrast, saturation, warmth, sharpen, blur, with live preview
- **Filters** — grayscale, black & white, invert, sepia, vintage, sketch, pencil, cartoon, emboss, warm, cool
- **Geometry** — rotate (90° / 180° / any angle), flip, resize with aspect-ratio lock, drag-to-crop
- **Advanced** — auto-enhance, edge detection with live Canny thresholds, face detection (sensitivity, minimum face size, box colour, line width, confidence labels, facial landmarks)

**Batch processing**
- Resize, convert format, and watermark a whole folder; the three operations stack
- Output goes to a separate folder — **your originals are never modified**
- Supports **pause, resume, and stop**

**Other**
- **18 output formats**: `jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`
- **Full support for non-ASCII (e.g. Chinese) file paths**
- Undo / redo, hold-to-view-original, automatic canvas centring
- Every panel has its own independent Apply / Reset — changes never leak between panels

## ⚠️ Disclaimer

**Downloading or using this software means you understand and accept the following.**

1. **No warranty.** This software is provided **"AS IS"**, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, accuracy, and non-infringement. It may contain defects or exhibit unexpected behaviour.
2. **Use at your own risk.** To the maximum extent permitted by law, the author and contributors shall not be liable for any loss or damage, including but not limited to corrupted images, loss of image quality, lost metadata, files overwritten or accidentally deleted, data loss, device failure, business interruption, or any direct, indirect, incidental, special, punitive, or consequential damages.
3. **⚠️ Back up your original images before processing.** Resizing, lossy format conversion, and cropping **may cause irreversible quality loss**. Never work directly on your only copy.
4. **Detection results are indicative only.** Face and edge detection are based on statistical models and are not guaranteed to be accurate or complete; they may miss detections or produce false positives. They must not be used for security, identity verification, medical, or legal purposes.
5. **Lawful use only.** You agree not to use this software for any unlawful purpose, including but not limited to collecting, processing, or recognising other people's facial images or biometric data without consent; infringing on portrait rights, privacy, reputation, or intellectual property; or creating or distributing illegal content. You are responsible for holding the legal rights to any image you process.
6. **Not affiliated with OpenCV.** This software uses the OpenCV library but has no affiliation, sponsorship, or endorsement relationship with OpenCV.org. It is an independent third-party work, not an official product. The OpenCV name and trademarks belong to their respective owners.
7. **Third-party components** (OpenCV / NumPy / Pillow / Python / YuNet face detection model) are provided under their own original licences, may carry additional terms, and likewise come with **no warranty**.
8. **Privacy.** This software contains **no networking functionality whatsoever**. It does not collect, upload, or store any of your images or usage data. All processing happens in local memory.

The full disclaimer is in the [README](https://github.com/evan-rio/image-tool/blob/main/README.md#️-disclaimer).

## Licence

MIT License — see [LICENSE](https://github.com/evan-rio/image-tool/blob/main/LICENSE).

---

<details>
<summary><strong>中文说明（点击展开）</strong></summary>

## 下载

| 平台 | 文件 | 说明 |
|---|---|---|
| **Windows** | `image-tool-1.0.7-windows-setup.exe` | 安装包，创建开始菜单和桌面快捷方式 |
| **Windows** | `image-tool-1.0.7-windows-portable.zip` | 便携版，解压即用，免安装 |
| **macOS（M 系列）** | `image-tool-1.0.7-macos-arm64.dmg` | 打开后把图标拖进「应用程序」 |
| **macOS（Intel）** | `image-tool-1.0.7-macos-x86_64.dmg` | 适用于 Intel 芯片的 Mac |

macOS 版另有 `.zip` 压缩包可选。程序自带运行时，**不需要单独安装 Python**。

## 首次打开

本项目没有购买商业代码签名证书，第一次打开时系统会拦一下：

- **Windows**：SmartScreen 提示「Windows 已保护你的电脑」→ 点「**更多信息**」→「**仍要运行**」
- **macOS**：提示「无法验证开发者」→ 在图标上**右键 → 打开** → 弹窗里再点一次「**打开**」

只需操作一次，之后正常双击即可。

## 功能

**单张处理**
- **调色** —— 亮度、对比度、饱和度、色调、锐化、模糊，拖动即时预览
- **滤镜** —— 灰度、黑白、反色、怀旧褐色、复古、素描、铅笔画、卡通、浮雕、暖色调、冷色调
- **几何** —— 旋转（90° / 180° / 任意角度）、镜像、改尺寸（可锁定比例）、鼠标框选裁剪
- **高级** —— 自动增强、边缘检测（Canny 阈值实时可调）、人脸检测（灵敏度、最小人脸、框颜色、线宽、置信度、五官关键点均可调）

**批量处理**
- 整个文件夹的缩放 / 转格式 / 加水印，三种可叠加
- 结果输出到单独文件夹，**不改动原图**
- 支持**暂停、继续、停止**

**其他**
- **18 种输出格式**：`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`
- **完整支持中文路径**的读取与保存
- 撤销重做、按住看原图、画布自动居中
- 每个功能区各自独立的「应用 / 重置」，互不影响

## ⚠️ 免责声明

**下载或使用即表示你已理解并接受以下全部内容。**

1. **无担保。** 本软件按「原样」提供，不附带任何明示或暗示的担保，包括但不限于对适销性、特定用途适用性、准确性、不侵权的担保。软件可能存在缺陷或未预料的行为。
2. **使用风险自负。** 在法律允许的最大范围内，作者及贡献者不对任何损失或损害承担责任，包括但不限于图片损坏、画质损失、元数据丢失、文件被覆盖或误删、数据丢失、设备故障、业务中断，以及任何直接、间接、偶然、特殊、惩罚性或后果性的损害。
3. **⚠️ 处理前请务必备份原图。** 缩放、有损格式转换、裁剪等操作**可能造成不可逆的画质损失**，请勿在唯一的原件上直接操作。
4. **识别结果仅供参考。** 人脸检测、边缘检测基于统计模型，不保证准确或完整，可能漏检、误检或产生偏差，不可用于安全、身份核验、医疗、法律等严肃场景。
5. **禁止用于违法违规用途。** 你承诺不将本软件用于任何违法违规用途，包括但不限于：未经他人同意采集、处理或识别人脸图像及生物特征信息；侵犯他人的肖像权、隐私权、名誉权或知识产权；制作、传播违法违规内容。你应自行确保对所处理的图片拥有合法权利，并自行承担因侵权或违规产生的全部法律责任。
6. **与 OpenCV 官方无关。** 本软件使用了 OpenCV 库，但与 OpenCV.org 没有任何隶属、赞助或背书关系，是第三方独立作品，并非官方产品。OpenCV 的名称与商标归其各自所有者所有。
7. **第三方组件**（OpenCV / NumPy / Pillow / Python / YuNet 人脸检测模型）按其各自原许可提供，可能附带额外条款，且**同样不提供任何担保**。
8. **隐私。** 本软件不包含任何联网功能，不采集、不上传、不存储你的图片或使用数据，全部处理在本机内存中完成。

完整免责声明见仓库 [README](https://github.com/evan-rio/image-tool/blob/main/README.md)。

## 开源许可

MIT License，详见 [LICENSE](https://github.com/evan-rio/image-tool/blob/main/LICENSE)。

</details>
