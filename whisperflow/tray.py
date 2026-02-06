"""System tray icon for WhisperFlow.

Uses AyatanaAppIndicator3 (modern AppIndicator fork on Ubuntu/Zorin).
Falls back to a no-op tray if GTK/AppIndicator is unavailable.
"""

import threading

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import Gtk, GLib, AyatanaAppIndicator3

    HAS_GTK = True
except (ImportError, ValueError):
    HAS_GTK = False


class TrayIcon:
    """System tray icon showing WhisperFlow status."""

    # Icon names from standard GTK icon theme
    ICON_IDLE = "audio-input-microphone-symbolic"
    ICON_RECORDING = "media-record-symbolic"
    ICON_TRANSCRIBING = "emblem-synchronizing-symbolic"

    def __init__(self):
        self._indicator = None
        self._status_item = None
        self._thread = None
        self._quit_callback = None

        if not HAS_GTK:
            return

        self._indicator = AyatanaAppIndicator3.Indicator.new(
            "whisperflow",
            self.ICON_IDLE,
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_title("WhisperFlow")

        # Build menu
        menu = Gtk.Menu()

        self._status_item = Gtk.MenuItem(label="Status: Idle")
        self._status_item.set_sensitive(False)
        menu.append(self._status_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)

        menu.show_all()
        self._indicator.set_menu(menu)

    def set_recording(self):
        """Update tray to recording state."""
        self._update_icon(self.ICON_RECORDING, "Status: Recording...")

    def set_transcribing(self):
        """Update tray to transcribing state."""
        self._update_icon(self.ICON_TRANSCRIBING, "Status: Transcribing...")

    def set_idle(self, last_text=""):
        """Update tray to idle state."""
        label = "Status: Idle"
        if last_text:
            preview = last_text[:50] + ("..." if len(last_text) > 50 else "")
            label = f"Last: {preview}"
        self._update_icon(self.ICON_IDLE, label)

    def _update_icon(self, icon_name, status_text):
        """Thread-safe icon update via GLib.idle_add."""
        if not HAS_GTK or not self._indicator:
            return

        def _do_update():
            self._indicator.set_icon_full(icon_name, status_text)
            if self._status_item:
                self._status_item.set_label(status_text)
            return False  # Don't repeat

        GLib.idle_add(_do_update)

    def _on_quit(self, _widget):
        """Handle quit menu item."""
        if self._quit_callback:
            self._quit_callback()
        Gtk.main_quit()

    def run(self, quit_callback=None):
        """Start GTK main loop in a background thread.

        Args:
            quit_callback: Function to call when user clicks Quit.
        """
        self._quit_callback = quit_callback

        if not HAS_GTK:
            return

        self._thread = threading.Thread(target=Gtk.main, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the GTK main loop."""
        if HAS_GTK:
            GLib.idle_add(Gtk.main_quit)
