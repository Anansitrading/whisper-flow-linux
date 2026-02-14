"""Text injection module for WhisperFlow.

Platform support:
  - Linux/Wayland: wtype (direct) or wl-copy + wtype ctrl+v (clipboard)
  - Linux/X11: xdotool + xclip (clipboard paste)
  - Windows: ctypes SendInput (clipboard paste via Ctrl+V)
"""

import os
import sys
import subprocess
import shutil
import time

IS_WINDOWS = sys.platform == "win32"


def _has(cmd):
    return shutil.which(cmd) is not None


def _is_wayland():
    return os.environ.get("XDG_SESSION_TYPE") == "wayland" or \
           os.environ.get("WAYLAND_DISPLAY") is not None


def type_text(text, delay_ms=10, prepend_space=True):
    """Type text at the current cursor position in the focused window."""
    if not text:
        return

    if prepend_space:
        text = " " + text

    if IS_WINDOWS:
        _type_windows(text)
    elif _is_wayland() and _has("xdotool"):
        _type_x11(text, delay_ms)
    elif _is_wayland():
        _type_wayland(text, delay_ms)
    else:
        _type_x11(text, delay_ms)


# ─── Windows ────────────────────────────────────────────────────────────────

def _type_windows(text):
    """Type on Windows using clipboard paste (Ctrl+V) via ctypes."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    # Set proper return/argument types for 64-bit correctness.
    # Without this, ctypes defaults to c_int (32-bit) which truncates
    # 64-bit handles and pointers, causing access violations.
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]

    def _set_clipboard_text(txt):
        """Encode text and place it on the already-opened clipboard."""
        user32.EmptyClipboard()
        encoded = txt.encode("utf-16-le") + b"\x00\x00"
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not h_mem:
            return False
        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            return False
        ctypes.memmove(ptr, encoded, len(encoded))
        kernel32.GlobalUnlock(h_mem)
        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        return True

    # --- Save old clipboard ---
    old_clipboard = None
    if user32.OpenClipboard(0):
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if h:
            ptr = kernel32.GlobalLock(h)
            if ptr:
                old_clipboard = ctypes.wstring_at(ptr)
                kernel32.GlobalUnlock(h)
        user32.CloseClipboard()

    # --- Set new clipboard text ---
    if user32.OpenClipboard(0):
        ok = _set_clipboard_text(text)
        user32.CloseClipboard()
        if not ok:
            return
    else:
        return

    # --- Send Ctrl+V via SendInput ---
    time.sleep(0.05)  # Small delay for clipboard to settle
    _send_ctrl_v()

    # --- Restore old clipboard ---
    if old_clipboard is not None:
        time.sleep(0.1)
        if user32.OpenClipboard(0):
            _set_clipboard_text(old_clipboard)
            user32.CloseClipboard()


def _send_ctrl_v():
    """Send Ctrl+V keystroke using SendInput on Windows."""
    import ctypes
    from ctypes import wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_V = 0x56

    # ULONG_PTR is pointer-sized unsigned int (8 bytes on 64-bit Windows)
    ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [
                ("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT),
            ]
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT),
        ]

    def _make_key_input(vk, flags=0):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp._input.ki.wVk = vk
        inp._input.ki.wScan = 0
        inp._input.ki.dwFlags = flags
        inp._input.ki.time = 0
        inp._input.ki.dwExtraInfo = None
        return inp

    # Ctrl down, V down, V up, Ctrl up
    inputs = [
        _make_key_input(VK_CONTROL),
        _make_key_input(VK_V),
        _make_key_input(VK_V, KEYEVENTF_KEYUP),
        _make_key_input(VK_CONTROL, KEYEVENTF_KEYUP),
    ]

    arr = (INPUT * len(inputs))(*inputs)
    ctypes.windll.user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


# ─── Linux / Wayland ────────────────────────────────────────────────────────

def _type_wayland(text, delay_ms):
    """Type on Wayland using wtype or wl-clipboard fallback."""
    if _has("wl-copy") and _has("wtype"):
        _wayland_clipboard_paste(text)
    elif _has("wtype"):
        subprocess.run(
            ["wtype", "-d", str(delay_ms), text],
            check=False, timeout=30,
        )
    else:
        raise RuntimeError(
            "No Wayland typing tool found. Install wtype: sudo apt install wtype"
        )


def _wayland_clipboard_paste(text):
    """Paste via Wayland clipboard for best Unicode support."""
    try:
        old = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except Exception:
        old = None

    subprocess.run(
        ["wl-copy", "--", text],
        check=False, timeout=2,
    )
    subprocess.run(
        ["wtype", "-M", "ctrl", "-P", "v", "-p", "v", "-m", "ctrl"],
        check=False, timeout=5,
    )

    if old is not None:
        time.sleep(0.1)
        subprocess.run(
            ["wl-copy", "--", old],
            check=False, timeout=2,
        )


# ─── Linux / X11 ────────────────────────────────────────────────────────────

def _get_focused_wm_class():
    """Return the WM_CLASS string of the focused window, or empty string."""
    try:
        win_id = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=2,
        ).stdout.strip()
        result = subprocess.run(
            ["xprop", "-id", win_id, "WM_CLASS"],
            capture_output=True, text=True, timeout=2,
        )
        return result.stdout.strip().lower()
    except Exception:
        return ""


def _is_terminal_focused(wm_class=None):
    """Check if the currently focused window is a terminal emulator."""
    if wm_class is None:
        wm_class = _get_focused_wm_class()
    terminal_keywords = [
        "terminal", "konsole", "xterm", "urxvt", "alacritty",
        "kitty", "terminator", "tilix", "sakura", "guake",
        "tilda", "foot", "wezterm", "hyper", "tabby", "rio",
        "ghostty", "contour", "lxterminal", "st-256color",
    ]
    return any(kw in wm_class for kw in terminal_keywords)


def _is_remote_viewer_focused(wm_class=None):
    """Check if the focused window is a VNC/RDP viewer where clipboard paste won't work."""
    if wm_class is None:
        wm_class = _get_focused_wm_class()
    remote_keywords = [
        "vncviewer", "tigervnc", "realvnc", "tightvnc",
        "remmina", "vinagre", "krdc", "xfreerdp", "rdesktop",
    ]
    return any(kw in wm_class for kw in remote_keywords)


def _type_x11(text, delay_ms):
    """Type on X11 using xdotool."""
    if not _has("xdotool"):
        raise RuntimeError(
            "xdotool not found. Install it: sudo apt install xdotool"
        )

    wm_class = _get_focused_wm_class()

    if _is_remote_viewer_focused(wm_class):
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay",
             str(max(delay_ms, 12)), text],
            check=False, timeout=30,
        )
        return

    if _has("xclip"):
        try:
            old = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True, text=True, timeout=2,
            ).stdout
        except Exception:
            old = None

        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text, text=True, timeout=2, check=False,
        )
        if _is_terminal_focused(wm_class):
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+shift+v"],
                check=False, timeout=5,
            )
        else:
            subprocess.run(
                ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
                check=False, timeout=5,
            )
        if old is not None:
            time.sleep(0.1)
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=old, text=True, timeout=2, check=False,
            )
    else:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", str(delay_ms), text],
            check=False, timeout=30,
        )
