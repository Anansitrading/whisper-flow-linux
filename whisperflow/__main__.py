"""WhisperFlow Linux - Main entry point.

Push-to-talk speech-to-text that types anywhere your cursor is.
"""

import argparse
import signal
import sys
import threading
import time

from whisperflow.config import load_config, ensure_config_exists
from whisperflow.audio import AudioRecorder, find_input_device
from whisperflow.transcriber import Transcriber
from whisperflow.hotkey import HotkeyListener
from whisperflow.typer import type_text
from whisperflow.tray import TrayIcon


class WhisperFlow:
    """Main application controller."""

    def __init__(self, config):
        self.config = config
        self._running = False
        self._transcribing = False

        # Initialize components
        device = find_input_device(config["audio_device"])
        self.recorder = AudioRecorder(
            device=device,
            sample_rate=config["sample_rate"],
        )
        self.transcriber = Transcriber(
            model_size=config["model"],
            compute_type=config["compute_type"],
            language=config["language"],
        )
        self.tray = TrayIcon()
        self.hotkey = HotkeyListener(
            hotkey_str=config["hotkey"],
            on_activate=self._on_record_start,
            on_deactivate=self._on_record_stop,
        )

    def _on_record_start(self):
        """Called when hotkey is pressed - start recording."""
        if self._transcribing:
            return
        self.recorder.start()
        self.tray.set_recording()
        _log("Recording...")

    def _on_record_stop(self):
        """Called when hotkey is released - stop recording and transcribe."""
        if self._transcribing:
            return

        audio = self.recorder.stop()
        duration = len(audio) / self.config["sample_rate"] if len(audio) > 0 else 0

        if duration < self.config["min_duration"]:
            self.tray.set_idle()
            return

        # Transcribe in background thread to avoid blocking hotkey listener
        self._transcribing = True
        self.tray.set_transcribing()

        def _do_transcribe():
            try:
                _log(f"Transcribing {duration:.1f}s of audio...")
                text = self.transcriber.transcribe(audio)
                if text:
                    _log(f"Result: {text}")
                    type_text(
                        text,
                        delay_ms=self.config["typing_delay_ms"],
                        prepend_space=self.config["prepend_space"],
                    )
                    self.tray.set_idle(last_text=text)
                else:
                    _log("No speech detected")
                    self.tray.set_idle()
            except Exception as e:
                _log(f"Transcription error: {e}")
                self.tray.set_idle()
            finally:
                self._transcribing = False

        threading.Thread(target=_do_transcribe, daemon=True).start()

    def run(self):
        """Start WhisperFlow."""
        self._running = True

        # Pre-load the Whisper model
        _log("Loading Whisper model...")
        self.transcriber._ensure_model()
        _log("Model loaded!")

        # Start components
        self.tray.run(quit_callback=self.stop)
        self.hotkey.start()

        # Open the audio stream so it's ready
        self.recorder.start()
        self.recorder.stop()  # Stop recording but keep stream open

        _log(f"WhisperFlow ready! Hold [{self.config['hotkey']}] to dictate.")
        _log("Speak while holding the hotkey, release to transcribe and type.")

        # Keep main thread alive
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop WhisperFlow."""
        _log("Shutting down...")
        self._running = False
        self.hotkey.stop()
        self.recorder.close()
        self.tray.stop()


def _log(msg):
    print(f"[WhisperFlow] {msg}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="WhisperFlow - Push-to-talk speech-to-text for Linux"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to config file (default: ~/.config/whisperflow/config.yaml)",
    )
    parser.add_argument(
        "--hotkey",
        help="Override hotkey (e.g., 'super+shift', 'ctrl+alt')",
    )
    parser.add_argument(
        "--model",
        help="Override Whisper model (tiny.en, base.en, small.en, medium.en)",
    )
    parser.add_argument(
        "--device",
        help="Audio device ('auto', 'default', or device index)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )
    args = parser.parse_args()

    # Detect session type for proper typing method
    import os
    session_type = os.environ.get("XDG_SESSION_TYPE", "")
    if not session_type:
        # Try to detect from loginctl
        try:
            import subprocess
            result = subprocess.run(
                ["loginctl", "show-session", "", "-p", "Type", "--value"],
                capture_output=True, text=True, timeout=2,
            )
            session_type = result.stdout.strip()
            if session_type:
                os.environ["XDG_SESSION_TYPE"] = session_type
        except Exception:
            pass

    if args.list_devices:
        import sounddevice as sd
        devices = sd.query_devices()
        print("Available input devices:")
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                marker = " <-- Blue Yeti" if "yeti" in d["name"].lower() else ""
                print(f"  [{i}] {d['name']} (channels={d['max_input_channels']}, sr={d['default_samplerate']}){marker}")
        return

    # Load config
    ensure_config_exists()
    config = load_config(args.config)

    # Apply CLI overrides
    if args.hotkey:
        config["hotkey"] = args.hotkey
    if args.model:
        config["model"] = args.model
    if args.device:
        config["audio_device"] = args.device

    _log(f"Config: model={config['model']}, hotkey={config['hotkey']}, device={config['audio_device']}")

    # Check input group membership (required for evdev hotkey detection)
    import grp
    try:
        input_members = grp.getgrnam("input").gr_mem
        import getpass
        username = getpass.getuser()
        if username not in input_members:
            # Also check primary group
            import os
            user_gids = os.getgroups()
            input_gid = grp.getgrnam("input").gr_gid
            if input_gid not in user_gids:
                _log("WARNING: You are not in the 'input' group.")
                _log("  Hotkey detection will not work!")
                _log("  Fix: sudo usermod -aG input $USER")
                _log("  Then log out and back in.")
                sys.exit(1)
    except KeyError:
        pass  # No 'input' group on this system

    # Handle signals
    app = WhisperFlow(config)
    signal.signal(signal.SIGTERM, lambda *_: app.stop())

    app.run()


if __name__ == "__main__":
    main()
