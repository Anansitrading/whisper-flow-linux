# WhisperFlow

Local, privacy-first push-to-talk speech-to-text for **Linux** and **Windows**. Hold a hotkey, speak, release - your words appear wherever your cursor is.

**No cloud services. No subscriptions. Everything runs on your machine.**

## How It Works

1. Hold **Ctrl+Shift** (configurable)
2. Speak into your microphone
3. Release the keys
4. Transcribed text is typed at your cursor position - in any application

Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2 backend) for fast local inference.

## Features

- **Push-to-talk** - Hold hotkey to record, release to transcribe and type
- **Works everywhere** - Types into any application (browsers, editors, terminals, chat)
- **System tray** - Minimal indicator shows status (idle/recording/transcribing)
- **Blue Yeti optimized** - Auto-detects Blue Yeti USB mic, works with any mic
- **Fast** - ~2-3 second transcription latency with base.en model on CPU
- **Private** - All audio processing happens locally, nothing leaves your machine
- **Configurable** - Custom hotkeys, model sizes, audio devices
- **Cross-platform** - Works on Linux (X11/Wayland) and Windows 10/11

---

## Windows Installation

### Requirements
- **OS:** Windows 10 or 11
- **Python:** 3.10+ ([Download](https://www.python.org/downloads/) - check "Add Python to PATH" during install)
- **RAM:** 1GB+ available (model uses ~200MB)
- **Microphone:** Any USB or built-in mic

### Quick Install (Windows)

```cmd
git clone https://github.com/Anansitrading/whisper-flow-linux.git
cd whisper-flow-linux
install-windows.bat
```

### Manual Install (Windows)

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m whisperflow
```

### Build Standalone .exe (Windows)

To create a distributable folder (no Python install needed on target machine):

```cmd
build-exe.bat
```

Output: `dist\WhisperFlow\` folder - zip it and share. Your friend runs `WhisperFlow.exe`.

### Windows Usage

```cmd
whisperflow-run.bat                    REM Start with defaults
whisperflow-run.bat --list-devices     REM Show audio devices
whisperflow-run.bat --hotkey f10       REM Use F10 as hotkey
whisperflow-run.bat --model small.en   REM Use larger model
```

Config file: `%APPDATA%\WhisperFlow\config.yaml`

---

## Linux Installation

### Requirements
- **OS:** Ubuntu 22.04+ / Zorin OS 17+ / Debian-based (X11 or Wayland)
- **Python:** 3.10+
- **RAM:** 1GB+ available (model uses ~200MB)
- **Microphone:** Any (Blue Yeti USB recommended)

### Quick Install (Linux)

```bash
git clone https://github.com/Anansitrading/whisper-flow-linux.git
cd whisper-flow-linux
chmod +x install.sh
./install.sh
```

### Manual Install (Linux)

```bash
# System dependencies
sudo apt install portaudio19-dev xdotool xclip gir1.2-ayatanaappindicator3-0.1

# Add to input group (required for hotkey detection)
sudo usermod -aG input $USER
# Log out and back in

# Python setup
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# Run
python -m whisperflow
```

### Linux Usage

```bash
./whisperflow-run.sh                     # Start with defaults
./whisperflow-run.sh --list-devices      # Show audio devices
./whisperflow-run.sh --hotkey super+shift # Use Super+Shift
./whisperflow-run.sh --model small.en    # Use larger model
```

Config file: `~/.config/whisperflow/config.yaml`

### AppImage (Linux)

A self-contained AppImage is available for Linux:

```bash
chmod +x WhisperFlow-x86_64.AppImage
./WhisperFlow-x86_64.AppImage
```

Build your own: `./build-appimage.sh`

---

## Configuration

Edit the config file to customize behavior:

| Setting | Default | Description |
|---------|---------|-------------|
| `hotkey` | `ctrl+shift` | Hold to record, release to transcribe |
| `model` | `base.en` | Whisper model: `tiny.en`, `base.en`, `small.en`, `medium.en` |
| `compute_type` | `int8` | CPU inference: `int8` (fastest), `float32` |
| `audio_device` | `auto` | `auto`, `default`, or device index number |
| `sample_rate` | `16000` | 16kHz optimal for Whisper |
| `typing_delay_ms` | `10` | Delay between typed characters |
| `prepend_space` | `true` | Add space before typed text |
| `min_duration` | `0.3` | Ignore recordings shorter than this (seconds) |
| `language` | `en` | Transcription language |

### Hotkey Options

| Hotkey | Config Value | Notes |
|--------|-------------|-------|
| Ctrl + Shift | `ctrl+shift` | Default, works on both platforms |
| Ctrl + Alt | `ctrl+alt` | |
| Super + Shift | `super+shift` | Super = Windows key |
| Right Ctrl | `ctrl_r` | Good for single-key activation |
| F10 | `f10` | Function key, no modifier needed |
| Scroll Lock | `scrolllock` | Dedicated key, no conflicts |

---

## Troubleshooting

### Windows

**No audio captured:**
- Open Sound Settings > ensure your mic is set as default input
- Run `whisperflow-run.bat --list-devices` to find your mic
- Set the device index in config: `audio_device: 6`

**Hotkey not working:**
- Try a different hotkey: `whisperflow-run.bat --hotkey f10`
- Some antivirus may block keyboard hooks - add an exception for WhisperFlow

**Windows Defender flags the .exe:**
- This is a false positive common with PyInstaller-built apps
- Add an exclusion: Windows Security > Virus & Threat Protection > Exclusions

### Linux

**No audio captured:**
- Check your mic is set as input device in Sound Settings
- Run `./whisperflow-run.sh --list-devices` to find your mic
- Set the device index in config: `audio_device: 6`

**Hotkey not working:**
- Ensure you're in the `input` group: `groups $USER`
- Fix: `sudo usermod -aG input $USER` then log out and back in

**xdotool not typing:**
- Ensure xdotool is installed: `sudo apt install xdotool xclip`
- On Wayland: install wtype: `sudo apt install wtype wl-clipboard`

**Tray icon not showing:**
- Install AppIndicator: `sudo apt install gnome-shell-extension-appindicator`
- Log out and back in

**Slow transcription:**
- Switch to `tiny.en` model for faster results (less accurate)
- Ensure no other heavy processes are using CPU

## License

MIT
