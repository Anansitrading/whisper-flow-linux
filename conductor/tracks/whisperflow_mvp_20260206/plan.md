# WhisperFlow MVP - Implementation Plan

## Phase 1: Foundation & Dependencies
> Setup project structure, install dependencies, verify hardware

- [ ] **Task 1.1:** Create project structure (whisperflow package, setup.py, requirements.txt)
- [ ] **Task 1.2:** Install system dependencies (portaudio, ffmpeg, xdotool, GTK libs)
- [ ] **Task 1.3:** Create Python venv and install pip dependencies
- [ ] **Task 1.4:** Verify Blue Yeti detection and audio capture test
- [ ] **Task 1.5:** Verify faster-whisper model download and basic transcription test

## Phase 2: Core Audio Pipeline
> Audio capture and Whisper transcription modules

- [ ] **Task 2.1:** Implement `config.py` - YAML config loading with defaults
- [ ] **Task 2.2:** Implement `audio.py` - Blue Yeti auto-detection and recording
- [ ] **Task 2.3:** Implement `transcriber.py` - faster-whisper model loading and transcription
- [ ] **Task 2.4:** Integration test: record 5s audio -> transcribe -> print text

## Phase 3: Input/Output Integration
> Hotkey detection and text injection

- [ ] **Task 3.1:** Implement `hotkey.py` - Global push-to-talk with pynput
- [ ] **Task 3.2:** Implement `typer.py` - xdotool text injection
- [ ] **Task 3.3:** Wire hotkey -> audio -> transcribe -> type pipeline in `__main__.py`
- [ ] **Task 3.4:** End-to-end test: hold key, speak, release, verify typed text

## Phase 4: System Tray & Polish
> System tray icon, configuration, and packaging

- [ ] **Task 4.1:** Implement `tray.py` - GTK AppIndicator3 system tray
- [ ] **Task 4.2:** Wire tray status updates to pipeline events
- [ ] **Task 4.3:** Add CLI argument parsing and config file creation
- [ ] **Task 4.4:** Create `install.sh` one-line installer script
- [ ] **Task 4.5:** Write comprehensive README.md
- [ ] **Task 4.6:** Final integration test and commit
