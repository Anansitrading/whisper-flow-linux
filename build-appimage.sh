#!/usr/bin/env bash
# Build WhisperFlow AppImage
# Usage: ./build-appimage.sh
set -e

PROJ="$(cd "$(dirname "$0")" && pwd)"
APPDIR="$PROJ/WhisperFlow.AppDir"
OUTPUT="$PROJ/WhisperFlow-x86_64.AppImage"

echo "=== Building WhisperFlow AppImage ==="

# Download appimagetool if missing
if [ ! -f "$PROJ/appimagetool" ]; then
    echo "[1/7] Downloading appimagetool..."
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O "$PROJ/appimagetool"
    chmod +x "$PROJ/appimagetool"
else
    echo "[1/7] appimagetool already present"
fi

# Clean previous build
rm -rf "$APPDIR"

# Create AppDir structure
echo "[2/7] Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin" \
         "$APPDIR/usr/lib/python3.10" \
         "$APPDIR/usr/lib/x86_64-linux-gnu" \
         "$APPDIR/usr/lib/girepository-1.0" \
         "$APPDIR/usr/share/whisperflow" \
         "$APPDIR/usr/share/icons/hicolor/scalable/apps"

# Create clean venv and install deps
echo "[3/7] Creating clean venv and installing dependencies..."
python3.10 -m venv "$PROJ/venv-build"
source "$PROJ/venv-build/bin/activate"
pip install --upgrade pip -q
pip install faster-whisper sounddevice numpy pynput PyYAML -q
# Copy system gi for GTK tray
cp -r /usr/lib/python3/dist-packages/gi "$PROJ/venv-build/lib/python3.10/site-packages/" 2>/dev/null
deactivate

# Copy into AppDir
echo "[4/7] Assembling AppDir..."
cp /usr/bin/python3.10 "$APPDIR/usr/bin/python3.10"
cp -r /usr/lib/python3.10/* "$APPDIR/usr/lib/python3.10/" 2>/dev/null
cp -r "$PROJ/venv-build/lib/python3.10/site-packages" "$APPDIR/usr/lib/python3.10/site-packages"
cp -r "$PROJ/whisperflow" "$APPDIR/usr/share/whisperflow/whisperflow"
cp "$PROJ/config.yaml" "$APPDIR/usr/share/whisperflow/"

# Shared libraries
for lib in /usr/lib/x86_64-linux-gnu/libpython3.10.so* \
           /usr/lib/x86_64-linux-gnu/libffi.so* \
           /usr/lib/x86_64-linux-gnu/libexpat.so*; do
    [ -f "$lib" ] && cp -L "$lib" "$APPDIR/usr/lib/x86_64-linux-gnu/"
done

# GI typelibs
for typelib in AyatanaAppIndicator3-0.1 Gtk-3.0 GLib-2.0 GObject-2.0 Gio-2.0 \
               Gdk-3.0 GdkPixbuf-2.0 cairo-1.0 Pango-1.0 Atk-1.0 HarfBuzz-0.0 \
               freetype2-2.0 GModule-2.0 DBusMenu-0.4; do
    src="/usr/lib/x86_64-linux-gnu/girepository-1.0/${typelib}.typelib"
    [ -f "$src" ] && cp "$src" "$APPDIR/usr/lib/girepository-1.0/"
done

# Bundle Whisper model
echo "[5/7] Bundling Whisper model..."
mkdir -p "$APPDIR/usr/share/whisperflow/models"
MODEL_SRC="$HOME/.cache/huggingface/hub/models--Systran--faster-whisper-base.en"
if [ -d "$MODEL_SRC" ]; then
    cp -r "$MODEL_SRC" "$APPDIR/usr/share/whisperflow/models/"
else
    echo "Warning: Model not cached. Will download on first run."
fi

# Create AppRun
echo "[6/7] Creating AppRun and metadata..."
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONHOME="${HERE}/usr"
export PYTHONPATH="${HERE}/usr/share/whisperflow:${HERE}/usr/lib/python3.10/site-packages:${HERE}/usr/lib/python3.10"
export PYTHONNOUSERSITE=1
export LD_LIBRARY_PATH="${HERE}/usr/lib/x86_64-linux-gnu:${HERE}/usr/lib/python3.10/site-packages/numpy.libs:${HERE}/usr/lib/python3.10/site-packages/onnxruntime/capi:${LD_LIBRARY_PATH}"
export GI_TYPELIB_PATH="${HERE}/usr/lib/girepository-1.0:/usr/lib/x86_64-linux-gnu/girepository-1.0:${GI_TYPELIB_PATH}"
export HF_HUB_CACHE="${HERE}/usr/share/whisperflow/models"
export HUGGINGFACE_HUB_CACHE="${HERE}/usr/share/whisperflow/models"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
exec "${HERE}/usr/bin/python3.10" -m whisperflow "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Desktop file
cat > "$APPDIR/whisperflow.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=WhisperFlow
GenericName=Speech to Text
Comment=Push-to-talk speech-to-text - types anywhere your cursor is
Exec=whisperflow
Icon=whisperflow
Terminal=false
Categories=Utility;Accessibility;
Keywords=speech;voice;dictation;whisper;transcription;microphone;
StartupNotify=true
DESKTOP

# Icon
cat > "$APPDIR/whisperflow.svg" << 'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#4A90D9"/><stop offset="100%" style="stop-color:#2C5F8A"/></linearGradient></defs>
  <circle cx="64" cy="64" r="60" fill="url(#bg)" stroke="#1a3a5c" stroke-width="2"/>
  <rect x="52" y="28" width="24" height="40" rx="12" fill="#fff" opacity="0.95"/>
  <line x1="64" y1="68" x2="64" y2="82" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.95"/>
  <path d="M48 62 Q48 78 64 78 Q80 78 80 62" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.95"/>
  <line x1="52" y1="82" x2="76" y2="82" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.95"/>
  <path d="M36 48 Q30 54 30 64 Q30 74 36 80" fill="none" stroke="#7ec8e3" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
  <path d="M92 48 Q98 54 98 64 Q98 74 92 80" fill="none" stroke="#7ec8e3" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
</svg>
SVG

cp "$APPDIR/whisperflow.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp "$APPDIR/whisperflow.svg" "$APPDIR/.DirIcon"
# Minimal PNG for compatibility
python3.10 -c "
import struct,zlib
def c(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
with open('$APPDIR/whisperflow.png','wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+c(b'IDAT',zlib.compress(b'\x00\x4a\x90\xd9'))+c(b'IEND',b''))
"

# Build AppImage
echo "[7/7] Building AppImage..."
ARCH=x86_64 "$PROJ/appimagetool" "$APPDIR" "$OUTPUT" 2>&1 | tail -5

# Cleanup
rm -rf "$APPDIR" "$PROJ/venv-build"

echo ""
echo "=== Built: $OUTPUT ($(du -h "$OUTPUT" | cut -f1)) ==="
echo "Install: cp $OUTPUT ~/Applications/ && chmod +x ~/Applications/WhisperFlow.AppImage"
