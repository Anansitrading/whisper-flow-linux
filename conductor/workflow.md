# WhisperFlow Linux - Development Workflow

## Development Process
1. Implement feature module
2. Test manually with Blue Yeti mic
3. Commit with conventional commit message

## Git Strategy
- Single `main` branch
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
- Commit after each completed module

## Testing Strategy
- Manual testing with live microphone (primary)
- Unit tests for config parsing and text processing
- Integration test: record -> transcribe -> verify output

## Quality Gates
- Code runs without errors on Zorin OS 17 with Python 3.10
- Audio capture works with Blue Yeti
- Transcription produces readable English text
- xdotool types correctly in target window
- System tray icon displays and responds to clicks
