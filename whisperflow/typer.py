"""Text injection module for WhisperFlow.

Types transcribed text at the current cursor position using xdotool.
Uses clipboard paste as fallback for Unicode/special characters.
Works in any X11 application.
"""

import subprocess
import shutil


def _has_command(cmd):
    return shutil.which(cmd) is not None


def type_text(text, delay_ms=10, prepend_space=True):
    """Type text at the current cursor position.

    Tries xdotool first. Falls back to xclip + Ctrl+V paste
    for better Unicode and special character support.

    Args:
        text: The text to type.
        delay_ms: Delay between keystrokes in milliseconds.
        prepend_space: Whether to add a leading space.
    """
    if not text:
        return

    if prepend_space:
        text = " " + text

    # Try clipboard paste for reliability with special chars
    if _has_command("xclip") and _has_command("xdotool"):
        _type_via_clipboard(text)
    elif _has_command("xdotool"):
        _type_via_xdotool(text, delay_ms)
    else:
        raise RuntimeError(
            "xdotool not found. Install it: sudo apt install xdotool"
        )


def _type_via_clipboard(text):
    """Paste text via clipboard (handles Unicode reliably)."""
    # Save current clipboard
    try:
        old_clip = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except Exception:
        old_clip = None

    # Set clipboard to our text
    subprocess.run(
        ["xclip", "-selection", "clipboard"],
        input=text, text=True, timeout=2, check=False,
    )

    # Paste with Ctrl+V
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
        check=False, timeout=5,
    )

    # Restore old clipboard after a brief delay
    if old_clip is not None:
        import time
        time.sleep(0.1)
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=old_clip, text=True, timeout=2, check=False,
        )


def _type_via_xdotool(text, delay_ms):
    """Type text character by character via xdotool."""
    subprocess.run(
        [
            "xdotool",
            "type",
            "--clearmodifiers",
            "--delay",
            str(delay_ms),
            text,
        ],
        check=False,
        timeout=30,
    )
