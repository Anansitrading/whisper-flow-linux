"""Text injection module for WhisperFlow.

Auto-detects Wayland vs X11 and uses the right tool:
  - Wayland: wtype (direct) or wl-copy + wtype ctrl+v (clipboard)
  - X11: xdotool
"""

import os
import subprocess
import shutil
import time


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

    if _is_wayland() and _has("xdotool"):
        # Many Wayland compositors don't support virtual keyboard protocol,
        # but xdotool still works via XWayland
        _type_x11(text, delay_ms)
    elif _is_wayland():
        _type_wayland(text, delay_ms)
    else:
        _type_x11(text, delay_ms)


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
    # Save old clipboard
    try:
        old = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except Exception:
        old = None

    # Set clipboard and paste
    subprocess.run(
        ["wl-copy", "--", text],
        check=False, timeout=2,
    )
    subprocess.run(
        ["wtype", "-M", "ctrl", "-P", "v", "-p", "v", "-m", "ctrl"],
        check=False, timeout=5,
    )

    # Restore old clipboard
    if old is not None:
        time.sleep(0.1)
        subprocess.run(
            ["wl-copy", "--", old],
            check=False, timeout=2,
        )


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

    # VNC/RDP viewers: clipboard paste won't work (local vs remote clipboard),
    # so use direct keystroke injection instead
    if _is_remote_viewer_focused(wm_class):
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay",
             str(max(delay_ms, 12)), text],
            check=False, timeout=30,
        )
        return

    if _has("xclip"):
        # Clipboard paste (better Unicode)
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
        # Terminals use Ctrl+Shift+V for paste; other apps use Ctrl+V
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
