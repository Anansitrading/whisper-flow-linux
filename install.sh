#!/usr/bin/env bash
# WhisperFlow Linux Installer
set -e

echo "=== WhisperFlow Linux Installer ==="
echo ""

if ! command -v apt-get &> /dev/null; then
    echo "Error: This installer requires apt-get (Debian/Ubuntu/Zorin OS)"
    exit 1
fi

# Install system dependencies
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-venv \
    python3-pip \
    portaudio19-dev \
    xdotool \
    xclip \
    wtype \
    wl-clipboard \
    gir1.2-ayatanaappindicator3-0.1 \
    libayatana-appindicator3-dev \
    2>/dev/null

if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get install -y -qq ffmpeg 2>/dev/null || true
fi

# Add user to input group (needed for push-to-talk hotkey via evdev)
echo "[2/6] Setting up input group for hotkey detection..."
if ! groups "$USER" | grep -q '\binput\b'; then
    sudo usermod -aG input "$USER"
    echo "  Added $USER to 'input' group."
    echo "  NOTE: You must log out and back in for this to take effect."
else
    echo "  Already in 'input' group."
fi

# Create venv
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[3/6] Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install Python dependencies
echo "[4/6] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Download Whisper model
echo "[5/6] Downloading Whisper base.en model (~74MB)..."
python3 -c "
from faster_whisper import WhisperModel
print('Downloading model...', flush=True)
model = WhisperModel('base.en', device='cpu', compute_type='int8')
print('Model ready!', flush=True)
"

# Create default config
echo "[6/6] Creating default configuration..."
python3 -c "from whisperflow.config import ensure_config_exists; ensure_config_exists()"

# Create launcher script
cat > "$INSTALL_DIR/whisperflow-run.sh" << 'LAUNCHER'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/venv/bin/activate"
exec python3 -m whisperflow "$@"
LAUNCHER
chmod +x "$INSTALL_DIR/whisperflow-run.sh"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "IMPORTANT: Log out and back in for 'input' group to take effect!"
echo ""
echo "Usage:"
echo "  ./whisperflow-run.sh              # Start WhisperFlow"
echo "  ./whisperflow-run.sh --list-devices  # Show audio devices"
echo ""
echo "Config: ~/.config/whisperflow/config.yaml"
echo "Default hotkey: Ctrl+Shift (hold to record, release to type)"
