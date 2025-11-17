"""Tkinter GUI for Personal Input Tracker."""
from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Callable, Optional
import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import pystray  # type: ignore
    from PIL import Image, ImageDraw  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pystray = None
    Image = None

from config import AppConfig

LOGGER = logging.getLogger(__name__)


class TrackerGUI:
    """Encapsulates tkinter windows and tray icon."""

    def __init__(
        self,
        config: AppConfig,
        start_callback: Callable[[], None],
        stop_callback: Callable[[], None],
        open_logs_callback: Callable[[], None],
        stats_provider: Callable[[], tuple[int, int]],
    ) -> None:
        self.config = config
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.open_logs_callback = open_logs_callback
        self.stats_provider = stats_provider
        self.root = tk.Tk()
        self.root.title("Personal Input Tracker")
        self.root.geometry("420x260")
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

        self.status_var = tk.StringVar(value="Disconnected")
        self.sent_var = tk.StringVar(value="0")
        self.pending_var = tk.StringVar(value="0")
        self.recording = False

        self._build_widgets()
        self._tray_icon: Optional[pystray.Icon] = None
        if self.config.tray_enabled and pystray and Image:
            self._init_tray()

        self._stop_event = Event()
        self._stats_thread = Thread(target=self._stats_loop, daemon=True)
        self._stats_thread.start()

    def _build_widgets(self) -> None:
        ttk.Label(self.root, text="Koneksi Server:").pack(anchor="w", padx=12, pady=(12, 0))
        ttk.Label(self.root, textvariable=self.status_var, font=("Arial", 12, "bold")).pack(
            anchor="w", padx=12
        )

        ttk.Label(self.root, text="Input terkirim:").pack(anchor="w", padx=12, pady=(12, 0))
        ttk.Label(self.root, textvariable=self.sent_var).pack(anchor="w", padx=12)

        ttk.Label(self.root, text="Input tertunda:").pack(anchor="w", padx=12, pady=(12, 0))
        ttk.Label(self.root, textvariable=self.pending_var).pack(anchor="w", padx=12)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", pady=20)
        self.start_button = ttk.Button(button_frame, text="Mulai", command=self.toggle_recording)
        self.start_button.pack(side="left", padx=10)

        ttk.Button(button_frame, text="Buka Log", command=self.open_logs_callback).pack(
            side="left", padx=10
        )

        ttk.Button(button_frame, text="Keluar", command=self._confirm_exit).pack(
            side="right", padx=10
        )

    def toggle_recording(self) -> None:
        if not self.recording:
            self.start_callback()
            self.status_var.set("Merekam & mencoba konek")
            self.start_button.config(text="Jeda")
        else:
            self.stop_callback()
            self.status_var.set("Berhenti sementara")
            self.start_button.config(text="Mulai")
        self.recording = not self.recording

    def open(self) -> None:
        self._show_ethics_warning()
        self.root.mainloop()

    def _confirm_exit(self) -> None:
        if messagebox.askyesno("Keluar", "Yakin ingin menutup aplikasi?"):
            self._cleanup()

    def _handle_close(self) -> None:
        if self.config.tray_enabled and pystray:
            self.root.withdraw()
        else:
            self._confirm_exit()

    def _cleanup(self) -> None:
        self._stop_event.set()
        self.stop_callback()
        if self._tray_icon:
            self._tray_icon.stop()
        self.root.destroy()

    def _stats_loop(self) -> None:
        while not self._stop_event.wait(1):
            sent, pending = self.stats_provider()
            self.sent_var.set(str(sent))
            self.pending_var.set(str(pending))
            self.status_var.set("Online" if pending == 0 else "Menunggu kirim")

    def _show_ethics_warning(self) -> None:
        if self.config.ethics_acknowledged:
            return
        message = (
            "PERINGATAN ETIKA:\n"
            "Gunakan alat ini hanya pada perangkat dan akun milik sendiri,"
            " dengan izin eksplisit dari pengguna terkait. Jangan gunakan"
            " untuk tujuan jahat atau memata-matai tanpa persetujuan."
        )
        messagebox.showwarning("Peringatan", message)

    def _init_tray(self) -> None:
        if not pystray or not Image:
            return
        image = self._generate_tray_image()
        if image is None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Tampilkan", lambda: self.root.after(0, self.root.deiconify)),
            pystray.MenuItem("Keluar", lambda: self.root.after(0, self._cleanup)),
        )
        self._tray_icon = pystray.Icon("tracker", image, "Input Tracker", menu)
        Thread(target=self._tray_icon.run, daemon=True).start()

    def _generate_tray_image(self):
        if not Image:
            return None
        size = 64
        image = Image.new("RGB", (size, size), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, size, size), fill="#3f51b5")
        draw.text((18, 20), "IT", fill="white")
        return image


def open_log_directory(path: Path) -> None:
    """Open log folder in OS file manager."""
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.call(["open", str(path)])
    else:
        subprocess.call(["xdg-open", str(path)])


__all__ = ["TrackerGUI", "open_log_directory"]
