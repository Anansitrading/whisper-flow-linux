# WhisperFlow Linux - Product Guidelines

## Naming
- Product name: **WhisperFlow Linux**
- CLI command: `whisperflow`
- Python package: `whisperflow`

## Tone & Voice
- Technical but approachable
- Documentation should be practical, not academic
- Error messages should suggest fixes

## Design Principles
1. **Invisible when idle** - System tray icon only, no persistent windows
2. **Instant feedback** - Visual indicator changes immediately on hotkey press
3. **Fail gracefully** - If mic disconnects or model fails, notify via tray, don't crash
4. **Respect privacy** - No audio leaves the machine, ever
