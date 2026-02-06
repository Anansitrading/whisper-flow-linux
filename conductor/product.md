# WhisperFlow Linux - Product Definition

## Vision
A local, privacy-first speech-to-text tool for Linux that transcribes speech and types it wherever the cursor is. No cloud services, no subscriptions - just hold a key and dictate.

## Target Users
- **Primary:** Linux desktop users (Ubuntu/Zorin OS) who want voice dictation in any application
- **Secondary:** Developers who want hands-free text input across editors, browsers, terminals, and chat apps

## Core Value Proposition
- **Local-only:** All processing on-device using OpenAI Whisper (faster-whisper)
- **Universal input:** Types transcribed text wherever the cursor is focused (any X11 window)
- **Push-to-talk:** Hold hotkey to record, release to transcribe and type - zero friction
- **Blue Yeti optimized:** Tuned for USB condenser microphones

## Key Features
1. Push-to-talk hotkey (hold to record, release to transcribe)
2. Local Whisper transcription (base.en model, CPU-optimized)
3. Types output at cursor position in any application (xdotool)
4. System tray icon with status indication (idle/recording/transcribing)
5. Configurable hotkey, model size, and audio device
6. Auto-start on login (optional)

## Success Metrics
- Transcription latency < 3 seconds after releasing hotkey
- Accurate English transcription in normal office noise levels
- Works in all X11 applications without special configuration
- CPU usage < 30% during idle, < 100% during transcription only

## Non-Goals
- Real-time streaming transcription (batch after release is fine)
- Multi-language support (English-only initially)
- Cloud/API fallback
- Wayland support (X11 only for v1)
