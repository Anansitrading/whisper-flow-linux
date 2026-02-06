# WhisperFlow MVP - Specification

## Overview
Build a complete push-to-talk speech-to-text application for Linux that captures audio from a Blue Yeti USB microphone, transcribes it locally using faster-whisper (base.en model), and types the result at the current cursor position in any X11 application. Includes a system tray icon for status feedback.

## Functional Requirements

### FR1: Audio Capture
- Capture audio from Blue Yeti USB mic via sounddevice
- Auto-detect Blue Yeti device index at startup
- Record at 16kHz mono float32 (Whisper's native format)
- Buffer audio in memory during recording (no disk writes)
- Handle mic disconnect gracefully (notification, no crash)

### FR2: Push-to-Talk Hotkey
- Global hotkey detection using pynput (X11)
- Default hotkey: Super+Shift (hold to record, release to stop)
- Configurable via config file
- Visual feedback: tray icon changes on press/release
- Debounce to prevent accidental triggers (< 300ms ignored)

### FR3: Whisper Transcription
- Use faster-whisper with base.en model
- CPU inference with int8 compute type
- Lazy model loading (load on first use, not startup)
- Transcribe captured audio buffer on hotkey release
- Return cleaned text (stripped whitespace, no hallucination artifacts)

### FR4: Text Injection
- Use xdotool to type transcribed text at cursor position
- Works in any X11 application (browsers, editors, terminals, chat)
- Add leading space if cursor is not at line start (configurable)
- Handle special characters properly
- Type with small delay (10ms) to prevent dropped characters

### FR5: System Tray Icon
- GTK AppIndicator3 system tray icon
- States: Idle (gray), Recording (red), Transcribing (yellow)
- Right-click menu: Settings info, Quit
- Tooltip shows current status and last transcription preview

### FR6: Configuration
- YAML config file at `~/.config/whisperflow/config.yaml`
- Configurable: hotkey, model size, audio device, typing delay
- Auto-create default config on first run
- Command-line override for any config option

### FR7: Application Lifecycle
- Run as background daemon
- Clean shutdown on SIGINT/SIGTERM
- Optional desktop entry for autostart
- Single instance enforcement (prevent duplicate processes)

## Non-Functional Requirements
- Transcription latency < 3 seconds on CPU
- Memory usage < 500MB (model + buffers)
- No network access required
- Works on Zorin OS 17.3 (Ubuntu 22.04 based)

## Acceptance Criteria
1. `whisperflow` command starts the application with tray icon
2. Holding Super+Shift records audio (tray turns red)
3. Releasing the hotkey transcribes and types text at cursor (tray turns yellow then gray)
4. Text appears correctly in gedit, Firefox, terminal, and VS Code
5. Blue Yeti mic is auto-detected without manual configuration
6. Application runs stably for 1+ hour session
