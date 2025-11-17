"""Utility helpers for the Personal Input Tracker."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List
import json
import logging
import platform

LOGGER = logging.getLogger(__name__)

try:  # Optional dependency
    import pygetwindow as gw  # type: ignore
except Exception:  # pragma: no cover - optional feature
    gw = None


def current_timestamp() -> str:
    """Return a human-friendly timestamp string."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def chunked(iterable: Iterable, size: int) -> Iterable[List]:
    """Yield lists of maximum length size from iterable."""
    chunk: List = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def get_active_window_title() -> str:
    """Try to detect the active window's title in a cross-platform way."""
    system = platform.system()
    try:
        if gw:
            window = gw.getActiveWindow()
            if window:
                return window.title or "Unknown"
        if system == "Windows":  # pragma: no cover - platform specific
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value
        if system == "Darwin":  # pragma: no cover - platform specific
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return active_app.localizedName()  # type: ignore[no-any-return]
        if system == "Linux":  # pragma: no cover - platform specific
            import subprocess
            result = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                window_id = result.stdout.strip().split()[-1]
                result = subprocess.run(
                    ["xprop", "-id", window_id, "_NET_WM_NAME"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    return result.stdout.split("\"", maxsplit=2)[1]
    except Exception as exc:  # pragma: no cover - best effort only
        LOGGER.debug("Unable to fetch window title: %s", exc)
    return "Unknown"


def looks_sensitive(title: str, keywords: List[str]) -> bool:
    """Return True if title suggests the user may enter sensitive info."""
    normalized = title.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


@dataclass
class PendingPayload:
    data: List[dict]

    def dump_to_file(self, path: Path) -> None:
        """Persist pending payload to newline-delimited JSON file."""
        lines = "\n".join(json.dumps(item) for item in self.data)
        path.write_text(lines + "\n", encoding="utf-8")

    @classmethod
    def load_from_file(cls, path: Path) -> "PendingPayload":
        """Load pending payload entries from disk, ignoring errors."""
        if not path.exists():
            return cls([])
        entries: List[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:  # pragma: no cover - defensive
                LOGGER.warning("Skipping malformed pending entry")
        return cls(entries)


__all__ = [
    "current_timestamp",
    "chunked",
    "get_active_window_title",
    "looks_sensitive",
    "PendingPayload",
]
