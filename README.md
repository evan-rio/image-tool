# OpenCV Image Tool

**English** | [简体中文](README.zh-CN.md)

A fully **offline** desktop image editor for Windows and macOS (Apple Silicon & Intel). Download and run — **no Python installation needed**. Everything happens on your own machine: no network access, no uploads, ever.

## Download

Grab the latest build from the **[Releases](../../releases/latest)** page:

| Platform | File |
|---|---|
| **Windows** | `…-windows-setup.exe` (installer) or `…-windows-portable.zip` |
| **macOS (Apple Silicon)** | `…-macos-arm64.dmg` |
| **macOS (Intel)** | `…-macos-x86_64.dmg` |

macOS builds are also available as `.zip` archives.

**First launch** — the app isn't code-signed, so the OS warns you once. Windows: click **More info → Run anyway**. macOS: **right-click the app → Open**, then **Open** again in the dialog.

## Features

### Single image

| Panel | Contents |
|---|---|
| **Adjust** | Brightness, contrast, saturation, warmth, sharpen, blur — live preview while dragging |
| **Filters** | Grayscale, black & white, invert, sepia, vintage, sketch, pencil, cartoon, emboss, warm, cool, oil paint, detail enhance, posterize, film grain, dehaze |
| **Enhance** | Denoise, sharpen / detail, local contrast (CLAHE), vignette — live preview |
| **Geometry** | Rotate (90° / 180° / any angle), flip, resize (aspect-ratio lock), drag-to-crop, four-point perspective correction |
| **Advanced** | Auto-enhance, edge detection (live Canny thresholds), face detection (sensitivity, minimum face size, box colour, line width, confidence labels, facial landmarks) |

### Batch processing

Resize, filter, enhance, convert format and watermark a whole folder. The operations stack, results go to a separate folder, and **your originals are never modified**. Supports pause, resume and stop.

### Other

- **Bilingual interface** — Simplified Chinese and English, follows your system language, switchable from the **Language** menu; your choice is remembered
- Each panel has its **own Apply / Reset** — panels never affect each other
- Undo / redo (20 steps), hold **View original** to compare
- Images are automatically centred on the canvas
- **macOS trackpad** — two-finger scroll pans, pinch zooms; **Command** + scroll also zooms
- **Full support for non-ASCII (e.g. Chinese) file paths**

### Output formats (18)

`jpg` `png` `webp` `avif` `bmp` `tif` `jp2` `gif` `ico` `pdf` `tga` `qoi` `hdr` `ppm` `pgm` `pbm` `pfm` `ras`

## Requirements

Windows 10 / 11 (64-bit) · macOS 11 or later · no separate Python installation

## Disclaimer

Provided **as is**, without warranty of any kind. Use at your own risk — the author is not liable for any loss or damage arising from its use.

**Back up your originals.** Resizing, lossy conversion and cropping can lose quality irreversibly; never work on your only copy.

Face and edge detection are statistical and may be wrong or incomplete — they must not be used for security, identity verification, medical or legal purposes.

Use it lawfully and only on images you have the rights to. The app has **no networking at all** — nothing is collected, uploaded or stored. Not affiliated with OpenCV.org.

## Build from source

> PyInstaller can't cross-compile: a macOS build needs macOS (or use the cloud build).

Local macOS build:

```bash
chmod +x build_mac.sh
./build_mac.sh arm64      # Apple Silicon
./build_mac.sh x86_64     # Intel
```

Cloud build (no Mac needed) — the workflow lives on the `packaging` branch and runs on `macos-14`; the Intel build is produced under Rosetta 2, so no Intel machine is required:

```bash
gh workflow run build-macos.yml --ref packaging
gh workflow run build-macos.yml --ref packaging -f publish=true   # also publish a Release
```

The release tag is read from `APP_VERSION` in `main.py`, so the tag, the filenames and the app version can never drift apart. Nothing passes through a local machine.

Self-test:

```bash
pip install -r requirements.txt
python selftest.py
```

## Third-party components

| Component | Purpose | Licence |
|---|---|---|
| [OpenCV](https://opencv.org/) | Core image processing | Apache License 2.0 |
| [NumPy](https://numpy.org/) | Array operations | BSD 3-Clause |
| [Pillow](https://python-pillow.org/) | Image codecs (AVIF / ICO / PDF / TGA / QOI) | MIT-CMU |
| [Python](https://www.python.org/) | Runtime | PSF License |
| [YuNet face model](https://github.com/opencv/opencv_zoo) | Face detection | Apache License 2.0 |

OpenCV is installed from PyPI (`opencv-python`) — this repository vendors no OpenCV source and patches nothing. OpenCV itself bundles further libraries (libjpeg-turbo, libpng, libtiff, libwebp, FFmpeg, …); their licence texts ship in the official distribution's `etc/licenses`. Official sources: [opencv/opencv](https://github.com/opencv/opencv) · [releases](https://github.com/opencv/opencv/releases) · [opencv_zoo](https://github.com/opencv/opencv_zoo).

## Licence

MIT — see [LICENSE](LICENSE).
