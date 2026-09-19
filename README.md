# OpenCV Image Tool

**English** | [简体中文](README.zh-CN.md)

A fully **offline** desktop image editor with a graphical interface. Available for Windows and macOS (Apple Silicon & Intel).

No Python installation required — download and run. All processing happens on your own machine: **no network access, no uploads, ever**.

---

## Download

Get the latest build from the **[Releases](../../releases/latest)** page:

| Platform | File | Notes |
|---|---|---|
| **Windows** | `image-tool-1.0.10-windows-setup.exe` | Installer — adds Start Menu and desktop shortcuts |
| **Windows** | `image-tool-1.0.10-windows-portable.zip` | Portable — unzip and run, no installation |
| **macOS (Apple Silicon)** | `image-tool-1.0.10-macos-arm64.dmg` | Open the DMG and drag the app to Applications |
| **macOS (Intel)** | `image-tool-1.0.10-macos-x86_64.dmg` | Same, for Intel-based Macs |

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
| **Filters** | Grayscale, black & white, invert, sepia, vintage, sketch, pencil, cartoon, emboss, warm, cool, oil paint, detail enhance, posterize, film grain, dehaze |
| **Enhance** | Denoise, sharpen / detail, local contrast (CLAHE), vignette — live preview |
| **Geometry** | Rotate (90° / 180° / any angle), flip horizontal & vertical, resize (aspect-ratio lock), drag-to-crop, four-point perspective correction |
| **Advanced** | Auto-enhance, edge detection (live Canny thresholds), face detection (sensitivity, minimum face size, box colour, line width, confidence labels, facial landmarks) |

### Batch processing

Resize, filter, enhance, convert format, and watermark an entire folder. The operations stack, results go to a separate output folder, and **your originals are never modified**. Supports **pause, resume, and stop**.

### Other

- **Bilingual interface** — Simplified Chinese and English. It follows your system language automatically, and you can switch any time from the **Language** menu; your choice is remembered
- Each panel has its **own Apply / Reset** — changes in one panel never affect another
- Undo / redo (20 steps)
- Hold **"View original"** to compare at any time
- Images are automatically centred on the canvas
- **macOS trackpad** — two-finger scroll pans the image, pinch zooms; hold **Command** and scroll to zoom too
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

The `build` branch holds the GitHub Actions workflow. It runs on `macos-14` (Apple Silicon) and produces both architectures — the Intel build is made by installing a python.org universal2 Python and running it under Rosetta 2, so no Intel machine and no `macos-13` queue is involved.

```bash
# build only
gh workflow run build-macos.yml --ref build

# build and publish a GitHub Release
gh workflow run build-macos.yml --ref build -f publish=true
```

With `publish=true` the runner uploads the `.dmg` and `.zip` straight to the release — nothing passes through a local machine. The release tag is taken from `APP_VERSION` in `main.py`, so the tag, the filenames and the app version can never drift apart.

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

### Where OpenCV comes from

**This repository does not vendor OpenCV's source code**, and there is no locally patched copy of it anywhere. The build installs OpenCV from PyPI (`opencv-python`), which ships the officially compiled binaries for each platform — the same thing every other project that uses OpenCV does.

That keeps this repository small enough to clone quickly and guarantees the OpenCV code always matches a released upstream version. If you want the source, it is here:

| Project | Official source |
|---|---|
| OpenCV library | [github.com/opencv/opencv](https://github.com/opencv/opencv) |
| OpenCV releases | [github.com/opencv/opencv/releases](https://github.com/opencv/opencv/releases) |
| Model zoo (YuNet and others) | [github.com/opencv/opencv_zoo](https://github.com/opencv/opencv_zoo) |

If you want to **change how the application itself works**, the whole program is `main.py` — see [Building from source](#building-from-source). No OpenCV source is involved at any point.

---

## Licence

Released under the **MIT License** — see [LICENSE](LICENSE).

You are free to use, modify, and distribute the source code, provided the copyright notice is retained. The source is likewise provided **without any warranty**.
