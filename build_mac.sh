#!/bin/bash
# ============================================================
#  图片处理软件 —— macOS 打包脚本
#
#  必须在 macOS 上运行（PyInstaller 不支持跨平台编译，
#  Windows 上无法生成 Mac 版）。
#
#  用法：
#    ./build_mac.sh              按当前机器架构打包（M 系列 → arm64）
#    ./build_mac.sh arm64        明确指定 M 系列芯片
#    ./build_mac.sh x86_64       只为 Intel Mac 打包
#    ./build_mac.sh universal2   同时支持两种芯片（需要 universal2 版 Python，
#                                且所有依赖都要有 universal2 wheel，不一定成功）
#
#  产物：dist/OpenCV 图片处理.app  和  dist/图片处理-1.0.0-mac-<架构>.dmg
# ============================================================

set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="OpenCV 图片处理"
BUNDLE_ID="com.photostudio.opencv-image-tool"
VERSION="1.0.0"
MODEL="models/face_detection_yunet_2023mar.onnx"

ARCH="${1:-$(uname -m)}"
PY="${PYTHON:-python3}"

echo "=========================================="
echo " 打包 macOS 版：$APP_NAME $VERSION"
echo " 目标架构：$ARCH"
echo "=========================================="

if [ "$(uname -s)" != "Darwin" ]; then
    echo "错误：本脚本必须在 macOS 上运行。"
    echo "PyInstaller 不支持交叉编译，没法在 Windows 上生成 Mac 版。"
    exit 1
fi

if ! command -v "$PY" > /dev/null 2>&1; then
    echo "错误：找不到 $PY"
    echo "请先安装 Python 3：https://www.python.org/downloads/macos/"
    exit 1
fi

if [ ! -f "$MODEL" ]; then
    echo "错误：缺少人脸检测模型 $MODEL"
    exit 1
fi

echo
echo "==> 1/5 检查 Python 环境"
"$PY" -c "import sys, platform; print('Python', sys.version.split()[0]); print('本机架构:', platform.machine())"

echo
echo "==> 2/5 安装依赖"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

echo
echo "==> 3/5 生成图标"
"$PY" make_icon.py

echo
echo "==> 4/5 打包 .app"
rm -rf build dist
"$PY" -m PyInstaller \
    --noconfirm --clean --windowed --onedir \
    --name "$APP_NAME" \
    --icon app.icns \
    --osx-bundle-identifier "$BUNDLE_ID" \
    --target-arch "$ARCH" \
    --add-data "app.icns:." \
    --add-data "app_icon.png:." \
    --add-data "$MODEL:models" \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --exclude-module pandas \
    --exclude-module pytest \
    --exclude-module PyQt5 \
    --exclude-module PySide2 \
    --noupx \
    main.py

APP="dist/$APP_NAME.app"
if [ ! -d "$APP" ]; then
    echo "错误：没有生成 $APP，请把上面的报错发我看看。"
    exit 1
fi

echo
echo "==> 5/5 临时签名 + 制作 dmg"

# 临时签名：没签名的 .app 会被 Gatekeeper 直接拦下
codesign --force --deep --sign - "$APP" > /dev/null 2>&1 \
    && echo "    已临时签名" \
    || echo "    临时签名失败（不影响本机右键打开）"

# 清掉从别处拷过来带的隔离标记
xattr -cr "$APP" 2>/dev/null || true

STAGE="dist/_dmg_stage"
rm -rf "$STAGE"
mkdir -p "$STAGE"
ditto "$APP" "$STAGE/$(basename "$APP")"
ln -s /Applications "$STAGE/Applications"

DMG="dist/图片处理-${VERSION}-mac-${ARCH}.dmg"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG" > /dev/null
rm -rf "$STAGE"

echo
echo "=========================================="
echo " 完成！"
echo "   应用：   $APP"
echo "   安装包： $DMG"
echo
echo " 双击 .app 即可运行。"
echo " 首次打开若提示「无法验证开发者」："
echo "   在图标上右键 -> 打开 -> 再点一次「打开」，之后就不再提示。"
echo "=========================================="
