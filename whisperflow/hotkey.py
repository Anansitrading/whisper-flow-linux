"""Global hotkey listener for push-to-talk.

Uses evdev to read keyboard events directly from /dev/input.
Works on both Wayland and X11. Requires user to be in 'input' group.
"""

import os
import threading
import evdev
from evdev import ecodes

# Map config key names to evdev key codes
_KEY_MAP = {
    "ctrl": {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL},
    "ctrl_l": {ecodes.KEY_LEFTCTRL},
    "ctrl_r": {ecodes.KEY_RIGHTCTRL},
    "shift": {ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT},
    "shift_l": {ecodes.KEY_LEFTSHIFT},
    "shift_r": {ecodes.KEY_RIGHTSHIFT},
    "alt": {ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT},
    "alt_l": {ecodes.KEY_LEFTALT},
    "alt_r": {ecodes.KEY_RIGHTALT},
    "super": {ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA},
    "super_l": {ecodes.KEY_LEFTMETA},
    "super_r": {ecodes.KEY_RIGHTMETA},
    "capslock": {ecodes.KEY_CAPSLOCK},
    "scrolllock": {ecodes.KEY_SCROLLLOCK},
    "pause": {ecodes.KEY_PAUSE},
    "f9": {ecodes.KEY_F9},
    "f10": {ecodes.KEY_F10},
    "f11": {ecodes.KEY_F11},
    "f12": {ecodes.KEY_F12},
}


def _find_keyboard():
    """Find the first keyboard device in /dev/input."""
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities(verbose=False)
            # Check if device has EV_KEY and common keyboard keys
            if ecodes.EV_KEY in caps:
                keys = caps[ecodes.EV_KEY]
                if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                    return dev
        except (PermissionError, OSError):
            continue
    return None


def parse_hotkey(hotkey_str):
    """Parse hotkey string like 'ctrl+shift' into list of evdev keycode sets."""
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    groups = []
    for part in parts:
        if part in _KEY_MAP:
            groups.append(_KEY_MAP[part])
        else:
            raise ValueError(
                f"Unknown key '{part}'. Available: {', '.join(sorted(_KEY_MAP.keys()))}"
            )
    return groups


class HotkeyListener:
    """Detects push-to-talk hotkey via evdev (Wayland + X11 compatible).

    Reads raw keyboard events from /dev/input. User must be in 'input' group.
    """

    def __init__(self, hotkey_str="ctrl+shift", on_activate=None, on_deactivate=None):
        self.hotkey_str = hotkey_str
        self.key_groups = parse_hotkey(hotkey_str)
        self.on_activate = on_activate or (lambda: None)
        self.on_deactivate = on_deactivate or (lambda: None)
        self._active = False
        self._pressed_groups = [False] * len(self.key_groups)
        self._thread = None
        self._running = False
        self._device = None

    def _matches_group(self, keycode, group_idx):
        return keycode in self.key_groups[group_idx]

    def _event_loop(self):
        self._device = _find_keyboard()
        if self._device is None:
            print(
                "[WhisperFlow] ERROR: No keyboard found in /dev/input/.\n"
                "  Fix: sudo usermod -aG input $USER  (then log out and back in)",
                flush=True,
            )
            return

        print(f"[WhisperFlow] Keyboard: {self._device.name}", flush=True)

        try:
            for event in self._device.read_loop():
                if not self._running:
                    break
                if event.type != ecodes.EV_KEY:
                    continue

                keycode = event.code
                # value: 0=up, 1=down, 2=repeat
                if event.value == 1:  # key down
                    for i in range(len(self.key_groups)):
                        if self._matches_group(keycode, i):
                            self._pressed_groups[i] = True

                    was_active = self._active
                    self._active = all(self._pressed_groups)
                    if self._active and not was_active:
                        self.on_activate()

                elif event.value == 0:  # key up
                    for i in range(len(self.key_groups)):
                        if self._matches_group(keycode, i):
                            self._pressed_groups[i] = False

                    was_active = self._active
                    self._active = all(self._pressed_groups)
                    if not self._active and was_active:
                        self.on_deactivate()

        except OSError:
            if self._running:
                print("[WhisperFlow] Keyboard disconnected.", flush=True)

    def start(self):
        """Start listening for hotkeys in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the hotkey listener."""
        self._running = False
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None
