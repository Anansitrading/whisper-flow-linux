"""Global hotkey listener for push-to-talk.

Uses pynput for X11 global key detection.
Supports configurable key combinations.
"""

import threading
from pynput import keyboard


# Map config strings to pynput key objects
_KEY_MAP = {
    "super": keyboard.Key.cmd,
    "super_l": keyboard.Key.cmd_l,
    "super_r": keyboard.Key.cmd_r,
    "shift": keyboard.Key.shift,
    "shift_l": keyboard.Key.shift_l,
    "shift_r": keyboard.Key.shift_r,
    "ctrl": keyboard.Key.ctrl,
    "ctrl_l": keyboard.Key.ctrl_l,
    "ctrl_r": keyboard.Key.ctrl_r,
    "alt": keyboard.Key.alt,
    "alt_l": keyboard.Key.alt_l,
    "alt_r": keyboard.Key.alt_r,
}

# Keys that match multiple variants (left or right)
_KEY_GROUPS = {
    "super": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
}


def parse_hotkey(hotkey_str):
    """Parse a hotkey string like 'super+shift' into a set of key groups.

    Returns a list of key group sets, where pressing any key in each group satisfies that part.
    """
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    groups = []
    for part in parts:
        if part in _KEY_GROUPS:
            groups.append(_KEY_GROUPS[part])
        elif part in _KEY_MAP:
            groups.append({_KEY_MAP[part]})
        else:
            # Try as a character key
            groups.append({keyboard.KeyCode.from_char(part)})
    return groups


class HotkeyListener:
    """Detects push-to-talk hotkey press and release.

    Calls on_activate when all hotkey keys are pressed,
    and on_deactivate when any is released.
    """

    def __init__(self, hotkey_str="super+shift", on_activate=None, on_deactivate=None):
        self.key_groups = parse_hotkey(hotkey_str)
        self.on_activate = on_activate or (lambda: None)
        self.on_deactivate = on_deactivate or (lambda: None)
        self._pressed_groups = [False] * len(self.key_groups)
        self._active = False
        self._lock = threading.Lock()
        self._listener = None

    def _matches_group(self, key, group_idx):
        """Check if a key matches any key in the given group."""
        group = self.key_groups[group_idx]
        if key in group:
            return True
        # Also check by value comparison for platform quirks
        for gkey in group:
            if hasattr(key, 'vk') and hasattr(gkey, 'vk'):
                if key.vk == gkey.vk:
                    return True
        return False

    def _on_press(self, key):
        with self._lock:
            for i in range(len(self.key_groups)):
                if self._matches_group(key, i):
                    self._pressed_groups[i] = True

            was_active = self._active
            self._active = all(self._pressed_groups)

            if self._active and not was_active:
                self.on_activate()

    def _on_release(self, key):
        with self._lock:
            for i in range(len(self.key_groups)):
                if self._matches_group(key, i):
                    self._pressed_groups[i] = False

            was_active = self._active
            self._active = all(self._pressed_groups)

            if not self._active and was_active:
                self.on_deactivate()

    def start(self):
        """Start listening for hotkeys in a background thread."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Stop the hotkey listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
