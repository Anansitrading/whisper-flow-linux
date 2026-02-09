"""System tray icon for WhisperFlow.

Platform support:
  - Linux: AyatanaAppIndicator3 (modern AppIndicator fork on Ubuntu/Zorin).
  - Windows: pystray + Pillow (native Windows system tray).
  - Falls back to a no-op tray if neither is available.
"""

import sys
import threading

IS_WINDOWS = sys.platform == "win32"

# ─── Linux GTK backend ──────────────────────────────────────────────────────

HAS_GTK = False
if not IS_WINDOWS:
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import Gtk, GLib, AyatanaAppIndicator3
        HAS_GTK = True
    except (ImportError, ValueError):
        pass

# ─── Windows pystray backend ────────────────────────────────────────────────

HAS_PYSTRAY = False
if IS_WINDOWS:
    try:
        import pystray
        from PIL import Image, ImageDraw
        HAS_PYSTRAY = True
    except ImportError:
        pass


class TrayIcon:
    """System tray icon showing WhisperFlow status."""

    # Icon names from standard GTK icon theme (Linux)
    ICON_IDLE = "audio-input-microphone-symbolic"
    ICON_RECORDING = "media-record-symbolic"
    ICON_TRANSCRIBING = "emblem-synchronizing-symbolic"

    def __init__(self):
        self._indicator = None  # Linux GTK
        self._status_item = None  # Linux GTK
        self._icon = None  # Windows pystray
        self._thread = None
        self._quit_callback = None

        if IS_WINDOWS and HAS_PYSTRAY:
            self._init_windows()
        elif HAS_GTK:
            self._init_linux()

    # ─── Linux GTK init ─────────────────────────────────────────────────

    def _init_linux(self):
        self._indicator = AyatanaAppIndicator3.Indicator.new(
            "whisperflow",
            self.ICON_IDLE,
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_title("WhisperFlow")

        menu = Gtk.Menu()

        self._status_item = Gtk.MenuItem(label="Status: Idle")
        self._status_item.set_sensitive(False)
        menu.append(self._status_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit_linux)
        menu.append(quit_item)

        menu.show_all()
        self._indicator.set_menu(menu)

    # ─── Windows pystray init ───────────────────────────────────────────

    def _init_windows(self):
        # Icon will be created on run() since pystray.Icon.run() blocks
        pass

    def _create_win_icon(self, state="idle"):
        """Create a colored icon image for the Windows system tray."""
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        colors = {
            "idle": (74, 144, 217),      # Blue
            "recording": (220, 50, 50),   # Red
            "transcribing": (255, 165, 0),  # Orange
        }
        color = colors.get(state, colors["idle"])

        # Draw filled circle
        draw.ellipse([4, 4, size - 4, size - 4], fill=color)
        # Draw inner microphone shape (simplified)
        cx, cy = size // 2, size // 2
        draw.rounded_rectangle(
            [cx - 6, cy - 16, cx + 6, cy + 4], radius=6, fill="white"
        )
        draw.line([cx, cy + 4, cx, cy + 12], fill="white", width=3)
        draw.arc([cx - 12, cy - 8, cx + 12, cy + 8], 0, 180, fill="white", width=2)

        return image

    # ─── Public API ─────────────────────────────────────────────────────

    def set_recording(self):
        """Update tray to recording state."""
        if IS_WINDOWS and HAS_PYSTRAY:
            self._update_icon_windows("recording", "WhisperFlow: Recording...")
        elif HAS_GTK:
            self._update_icon_linux(self.ICON_RECORDING, "Status: Recording...")

    def set_transcribing(self):
        """Update tray to transcribing state."""
        if IS_WINDOWS and HAS_PYSTRAY:
            self._update_icon_windows("transcribing", "WhisperFlow: Transcribing...")
        elif HAS_GTK:
            self._update_icon_linux(self.ICON_TRANSCRIBING, "Status: Transcribing...")

    def set_idle(self, last_text=""):
        """Update tray to idle state."""
        if last_text:
            preview = last_text[:50] + ("..." if len(last_text) > 50 else "")
            title = f"WhisperFlow: {preview}"
            label = f"Last: {preview}"
        else:
            title = "WhisperFlow: Idle"
            label = "Status: Idle"

        if IS_WINDOWS and HAS_PYSTRAY:
            self._update_icon_windows("idle", title)
        elif HAS_GTK:
            self._update_icon_linux(self.ICON_IDLE, label)

    # ─── Linux icon updates ─────────────────────────────────────────────

    def _update_icon_linux(self, icon_name, status_text):
        """Thread-safe icon update via GLib.idle_add."""
        if not self._indicator:
            return

        def _do_update():
            self._indicator.set_icon_full(icon_name, status_text)
            if self._status_item:
                self._status_item.set_label(status_text)
            return False

        GLib.idle_add(_do_update)

    def _on_quit_linux(self, _widget):
        if self._quit_callback:
            self._quit_callback()
        Gtk.main_quit()

    # ─── Windows icon updates ───────────────────────────────────────────

    def _update_icon_windows(self, state, title):
        """Update the Windows tray icon image and tooltip."""
        if self._icon:
            self._icon.icon = self._create_win_icon(state)
            self._icon.title = title

    def _on_quit_windows(self, icon, item):
        if self._quit_callback:
            self._quit_callback()
        icon.stop()

    # ─── Run / Stop ─────────────────────────────────────────────────────

    def run(self, quit_callback=None):
        """Start tray icon in a background thread."""
        self._quit_callback = quit_callback

        if IS_WINDOWS and HAS_PYSTRAY:
            menu = pystray.Menu(
                pystray.MenuItem("Quit WhisperFlow", self._on_quit_windows),
            )
            self._icon = pystray.Icon(
                "whisperflow",
                self._create_win_icon("idle"),
                "WhisperFlow: Idle",
                menu,
            )
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()
        elif HAS_GTK:
            self._thread = threading.Thread(target=Gtk.main, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the tray icon."""
        if IS_WINDOWS and HAS_PYSTRAY:
            if self._icon:
                self._icon.stop()
        elif HAS_GTK:
            GLib.idle_add(Gtk.main_quit)
