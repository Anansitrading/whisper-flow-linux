# WhisperFlow Linux - Tech Stack

## Language
- **Python 3.10+** (system Python on Zorin OS 17)

## Core Dependencies
| Library | Version | Purpose |
|---------|---------|---------|
| faster-whisper | latest | Local Whisper inference (CTranslate2 backend, CPU-optimized) |
| sounddevice | latest | Low-latency audio capture from Blue Yeti USB mic |
| numpy | latest | Audio buffer manipulation |
| pynput | latest | Global hotkey detection (X11) |
| PyGObject (gi) | system | GTK system tray icon (AppIndicator3) |

## System Dependencies
| Package | Purpose |
|---------|---------|
| xdotool | Type transcribed text at cursor position |
| portaudio19-dev | Audio backend for sounddevice |
| ffmpeg | Audio format support for faster-whisper |
| libappindicator3-dev | System tray support |
| gir1.2-appindicator3-0.1 | GTK AppIndicator bindings |

## Audio Configuration
- **Microphone:** Blue Yeti USB (ALSA card 1, PulseAudio source index 1)
- **PulseAudio source:** `alsa_input.usb-Blue_Microphones_Yeti_Stereo_Microphone_797_2019_09_05_77321-00.analog-stereo`
- **Sample rate:** 16000 Hz (Whisper's native rate)
- **Channels:** 1 (mono - downmixed from stereo)
- **Format:** float32

## Whisper Model
- **Default:** `base.en` (~74MB, ~2-3s CPU latency)
- **Device:** CPU (MX250 2GB VRAM insufficient)
- **Compute type:** int8 (fastest CPU inference)

## Architecture
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│  Hotkey      │───>│  Audio       │───>│  Whisper     │───>│  xdotool │
│  Listener    │    │  Recorder    │    │  Transcriber │    │  Typer   │
│  (pynput)    │    │  (sounddev)  │    │  (faster-w)  │    │          │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
       │                                       │
       └──────────── Tray Icon (GTK) ──────────┘
                     Status Updates
```

## Project Structure
```
whisper-flow-linux/
├── whisperflow/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── audio.py             # Audio capture (sounddevice)
│   ├── transcriber.py       # Whisper transcription
│   ├── typer.py             # xdotool text injection
│   ├── hotkey.py            # Global hotkey listener
│   ├── tray.py              # System tray icon
│   └── config.py            # Configuration management
├── config.yaml              # Default configuration
├── requirements.txt
├── setup.py
├── install.sh               # One-line installer
└── README.md
```
