#!/usr/bin/env bash
# WhisperFlow Linux Installer
# Installs system dependencies, creates venv, and sets up WhisperFlow
set -e

echo "=== WhisperFlow Linux Installer ==="
echo ""

# Check we're on a Debian-based system
if ! command -v apt-get &> /dev/null; then
    echo "Error: This installer requires apt-get (Debian/Ubuntu/Zorin OS)"
    exit 1
fi

# Install system dependencies
echo "[1/5] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-venv \
    python3-pip \
    portaudio19-dev \
    xdotool \
    xclip \
    gir1.2-ayatanaappindicator3-0.1 \
    libayatana-appindicator3-dev \
    2>/dev/null

# Check for ffmpeg (faster-whisper needs it for some formats, but we use raw audio)
if ! command -v ffmpeg &> /dev/null; then
    echo "Note: ffmpeg not found. Installing..."
    sudo apt-get install -y -qq ffmpeg 2>/dev/null || true
fi

# Create venv
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[2/5] Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install Python dependencies
echo "[3/5] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Download Whisper model
echo "[4/5] Downloading Whisper base.en model (~74MB)..."
python3 -c "
from faster_whisper import WhisperModel
import sys
print('Downloading model...', flush=True)
model = WhisperModel('base.en', device='cpu', compute_type='int8')
print('Model ready!', flush=True)
"

# Create default config
echo "[5/5] Creating default configuration..."
python3 -c "from whisperflow.config import ensure_config_exists; ensure_config_exists()"

# Create launcher script
cat > "$INSTALL_DIR/whisperflow-run.sh" << 'LAUNCHER'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/venv/bin/activate"
exec python3 -m whisperflow "$@"
LAUNCHER
chmod +x "$INSTALL_DIR/whisperflow-run.sh"

# Create desktop entry for autostart (optional)
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/whisperflow.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=WhisperFlow
Comment=Push-to-talk speech-to-text
Exec=$INSTALL_DIR/whisperflow-run.sh
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Accessibility;
DESKTOP

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Usage:"
echo "  ./whisperflow-run.sh              # Start WhisperFlow"
echo "  ./whisperflow-run.sh --list-devices  # Show audio devices"
echo "  ./whisperflow-run.sh --hotkey ctrl+shift  # Custom hotkey"
echo ""
echo "Config: ~/.config/whisperflow/config.yaml"
echo "Default hotkey: Super+Shift (hold to record, release to type)"
echo ""
echo "WhisperFlow has been added to your application menu."
