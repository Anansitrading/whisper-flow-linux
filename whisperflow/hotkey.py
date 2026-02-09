"""Global hotkey listener for push-to-talk.

Platform support:
  - Linux: evdev (/dev/input) - works on both Wayland and X11.
           Requires user to be in 'input' group.
  - Windows: pynput (low-level keyboard hook via SetWindowsHookEx).
"""

import os
import sys
import threading

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from pynput import keyboard as pynput_keyboard
else:
    import evdev
    from evdev import ecodes

# ─── Key mapping for Linux (evdev) ──────────────────────────────────────────

if not IS_WINDOWS:
    _KEY_MAP_LINUX = {
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

# ─── Key mapping for Windows (pynput) ───────────────────────────────────────

if IS_WINDOWS:
    _KEY_MAP_WINDOWS = {
        "ctrl": {pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r},
        "ctrl_l": {pynput_keyboard.Key.ctrl_l},
        "ctrl_r": {pynput_keyboard.Key.ctrl_r},
        "shift": {pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r, pynput_keyboard.Key.shift},
        "shift_l": {pynput_keyboard.Key.shift_l},
        "shift_r": {pynput_keyboard.Key.shift_r},
        "alt": {pynput_keyboard.Key.alt_l, pynput_keyboard.Key.alt_r, pynput_keyboard.Key.alt},
        "alt_l": {pynput_keyboard.Key.alt_l},
        "alt_r": {pynput_keyboard.Key.alt_r},
        "super": {pynput_keyboard.Key.cmd_l, pynput_keyboard.Key.cmd_r, pynput_keyboard.Key.cmd},
        "super_l": {pynput_keyboard.Key.cmd_l},
        "super_r": {pynput_keyboard.Key.cmd_r},
        "capslock": {pynput_keyboard.Key.caps_lock},
        "scrolllock": {pynput_keyboard.Key.scroll_lock},
        "pause": {pynput_keyboard.Key.pause},
        "f9": {pynput_keyboard.Key.f9},
        "f10": {pynput_keyboard.Key.f10},
        "f11": {pynput_keyboard.Key.f11},
        "f12": {pynput_keyboard.Key.f12},
    }


def _find_keyboard():
    """Find the first keyboard device in /dev/input (Linux only)."""
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities(verbose=False)
            if ecodes.EV_KEY in caps:
                keys = caps[ecodes.EV_KEY]
                if ecodes.KEY_A in keys and ecodes.KEY_Z in keys:
                    return dev
        except (PermissionError, OSError):
            continue
    return None


def parse_hotkey(hotkey_str):
    """Parse hotkey string like 'ctrl+shift' into list of keycode sets.

    Returns platform-specific keycode sets (evdev on Linux, pynput on Windows).
    """
    key_map = _KEY_MAP_WINDOWS if IS_WINDOWS else _KEY_MAP_LINUX
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    groups = []
    for part in parts:
        if part in key_map:
            groups.append(key_map[part])
        else:
            raise ValueError(
                f"Unknown key '{part}'. Available: {', '.join(sorted(key_map.keys()))}"
            )
    return groups


class HotkeyListener:
    """Detects push-to-talk hotkey.

    Linux: reads raw keyboard events from /dev/input via evdev.
    Windows: uses pynput low-level keyboard hook.
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
        self._device = None  # Linux only
        self._listener = None  # Windows only

    def _matches_group(self, keycode, group_idx):
        return keycode in self.key_groups[group_idx]

    # ─── Linux (evdev) ──────────────────────────────────────────────────

    def _event_loop_linux(self):
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

    # ─── Windows (pynput) ───────────────────────────────────────────────

    def _normalize_key(self, key):
        """Normalize a pynput key to match our key_groups sets."""
        # pynput gives us Key objects for special keys, KeyCode for regular keys
        if hasattr(key, 'name'):
            # It's a special key (Key.ctrl_l, Key.shift, etc.)
            return key
        return key

    def _on_press_windows(self, key):
        key = self._normalize_key(key)
        for i in range(len(self.key_groups)):
            if key in self.key_groups[i]:
                self._pressed_groups[i] = True

        was_active = self._active
        self._active = all(self._pressed_groups)
        if self._active and not was_active:
            self.on_activate()

    def _on_release_windows(self, key):
        key = self._normalize_key(key)
        for i in range(len(self.key_groups)):
            if key in self.key_groups[i]:
                self._pressed_groups[i] = False

        was_active = self._active
        self._active = all(self._pressed_groups)
        if not self._active and was_active:
            self.on_deactivate()

    # ─── Public API ─────────────────────────────────────────────────────

    def start(self):
        """Start listening for hotkeys in a background thread."""
        self._running = True
        if IS_WINDOWS:
            self._listener = pynput_keyboard.Listener(
                on_press=self._on_press_windows,
                on_release=self._on_release_windows,
            )
            self._listener.daemon = True
            self._listener.start()
        else:
            self._thread = threading.Thread(target=self._event_loop_linux, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the hotkey listener."""
        self._running = False
        if IS_WINDOWS:
            if self._listener:
                self._listener.stop()
                self._listener = None
        else:
            if self._device:
                try:
                    self._device.close()
                except Exception:
                    pass
                self._device = None
