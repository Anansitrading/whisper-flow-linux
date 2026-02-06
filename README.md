# WhisperFlow Linux

Local, privacy-first push-to-talk speech-to-text for Linux. Hold a hotkey, speak, release - your words appear wherever your cursor is.

**No cloud services. No subscriptions. Everything runs on your machine.**

## How It Works

1. Hold **Super+Shift** (configurable)
2. Speak into your microphone
3. Release the keys
4. Transcribed text is typed at your cursor position - in any application

Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2 backend) for fast local inference and `xdotool` for universal text input.

## Features

- **Push-to-talk** - Hold hotkey to record, release to transcribe and type
- **Works everywhere** - Types into any X11 application (browsers, editors, terminals, chat)
- **System tray** - Minimal indicator shows status (idle/recording/transcribing)
- **Blue Yeti optimized** - Auto-detects Blue Yeti USB mic, works with any mic
- **Fast** - ~2-3 second transcription latency with base.en model on CPU
- **Private** - All audio processing happens locally, nothing leaves your machine
- **Configurable** - Custom hotkeys, model sizes, audio devices

## Requirements

- **OS:** Ubuntu 22.04+ / Zorin OS 17+ (Debian-based with X11)
- **Python:** 3.10+
- **RAM:** 1GB+ available (model uses ~200MB)
- **Microphone:** Any (Blue Yeti USB recommended)

## Quick Install

```bash
git clone https://github.com/Anansitrading/whisper-flow-linux.git
cd whisper-flow-linux
chmod +x install.sh
./install.sh
```

## Manual Install

```bash
# System dependencies
sudo apt install portaudio19-dev xdotool xclip gir1.2-ayatanaappindicator3-0.1

# Python setup
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# Run
python -m whisperflow
```

## Usage

```bash
# Start with defaults (Super+Shift hotkey, base.en model)
./whisperflow-run.sh

# List audio devices
./whisperflow-run.sh --list-devices

# Custom hotkey
./whisperflow-run.sh --hotkey ctrl+shift

# Use a specific model
./whisperflow-run.sh --model small.en

# Specify audio device by index
./whisperflow-run.sh --device 6
```

## Configuration

Config file: `~/.config/whisperflow/config.yaml`

```yaml
hotkey: super+shift      # Hold to record, release to transcribe
model: base.en           # tiny.en, base.en, small.en, medium.en
compute_type: int8        # int8 (fastest CPU), float32
audio_device: auto        # auto, default, or device index
sample_rate: 16000        # 16kHz optimal for Whisper
typing_delay_ms: 10       # Delay between typed characters
prepend_space: true       # Add space before typed text
min_duration: 0.3         # Ignore recordings shorter than this
language: en              # Transcription language
```

## Hotkey Options

| Hotkey | Config Value |
|--------|-------------|
| Super + Shift | `super+shift` (default) |
| Ctrl + Shift | `ctrl+shift` |
| Ctrl + Alt | `ctrl+alt` |
| Right Ctrl | `ctrl_r` |

## Troubleshooting

**No audio captured:**
- Check Blue Yeti is set as input device in Sound Settings
- Run `./whisperflow-run.sh --list-devices` to find your mic
- Set the device index in config: `audio_device: 6`

**xdotool not typing:**
- Ensure you're running X11 (not Wayland): `echo $XDG_SESSION_TYPE`
- Install xclip for better compatibility: `sudo apt install xclip`

**Slow transcription:**
- Switch to `tiny.en` model for faster results (less accurate)
- Ensure no other heavy processes are using CPU

**Tray icon not showing:**
- Install AppIndicator extension: `sudo apt install gnome-shell-extension-appindicator`
- Log out and back in after installing

## License

MIT
