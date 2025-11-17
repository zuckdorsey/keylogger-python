"""Screenshot capturing helpers."""
from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Callable, Optional
import base64
import io
import logging
import time

from config import AppConfig

LOGGER = logging.getLogger(__name__)

try:  # Optional dependency
    import mss  # type: ignore
except Exception:  # pragma: no cover - optional fallback
    mss = None

try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - optional fallback
    pyautogui = None


class ScreenshotCapturer:
    """Capture screenshots periodically when enabled by config."""

    def __init__(self, config: AppConfig, callback: Callable[[dict], None]) -> None:
        self.config = config
        self.callback = callback
        self._thread: Optional[Thread] = None
        self._stop_event = Event()

    def start(self) -> None:
        if not self.config.enable_screenshots:
            LOGGER.debug("Screenshot capture disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="ScreenshotCapturer",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("Screenshot capture started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _capture(self) -> Optional[bytes]:
        if mss:
            from mss import tools  # type: ignore

            with mss.mss() as sct:  # type: ignore[attr-defined]
                screenshot = sct.grab(sct.monitors[0])
                return tools.to_png(screenshot.rgb, screenshot.size)
        if pyautogui:
            image = pyautogui.screenshot()
            buffer = io.BytesIO()
            image.save(buffer, format=self.config.screenshot_format.upper())
            return buffer.getvalue()
        LOGGER.debug("No screenshot backend available")
        return None

    def _run(self) -> None:
        interval = max(10, self.config.screenshot_interval_seconds)
        while not self._stop_event.wait(interval):
            raw = self._capture()
            if not raw:
                continue
            encoded = base64.b64encode(raw).decode("ascii")
            payload = {
                "type": "screenshot",
                "data": encoded,
                "format": self.config.screenshot_format,
            }
            self.callback(payload)


__all__ = ["ScreenshotCapturer"]
