"""Input logging module using pynput for keyboard and mouse."""
from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Thread
from typing import Callable, Dict, Optional
import logging

from pynput import keyboard, mouse  # type: ignore

from config import AppConfig
from utils import current_timestamp, get_active_window_title, looks_sensitive

LOGGER = logging.getLogger(__name__)

EventCallback = Callable[[Dict[str, str]], None]


def key_to_string(key: keyboard.Key | keyboard.KeyCode) -> str:
    """Convert pynput key to a human-friendly string."""
    try:
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char
        return str(key)
    except Exception:  # pragma: no cover - defensive
        return "unknown"


@dataclass
class InputLogger:
    """Manage keyboard/mouse listeners and emit normalized events."""

    config: AppConfig
    callback: EventCallback
    _keyboard_listener: Optional[keyboard.Listener] = None
    _mouse_listener: Optional[mouse.Listener] = None
    _stop_event: Event = Event()
    _thread: Optional[Thread] = None

    def start(self) -> None:
        """Start listener threads."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="InputLogger", daemon=True)
        self._thread.start()
        LOGGER.info("Input logger started")

    def stop(self) -> None:
        """Stop listeners gracefully."""
        self._stop_event.set()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
        LOGGER.info("Input logger stopped")

    def _run(self) -> None:
        """Create listeners and block until stop event is set."""
        self._keyboard_listener = keyboard.Listener(on_press=self._handle_key)
        self._mouse_listener = mouse.Listener(
            on_click=self._handle_click,
            on_scroll=self._handle_scroll,
        )
        self._keyboard_listener.start()
        self._mouse_listener.start()
        self._stop_event.wait()

    def _emit(self, payload: Dict[str, str]) -> None:
        """Enrich payload and call callback."""
        window_title = get_active_window_title()
        if looks_sensitive(window_title, self.config.sensitive_title_keywords):
            LOGGER.debug("Skipping event due to sensitive window: %s", window_title)
            return
        payload.update({
            "timestamp": current_timestamp(),
            "window": window_title,
        })
        self.callback(payload)
        if self.config.debug_mode:
            LOGGER.debug("Event: %s", payload)

    def _handle_key(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """Handle keyboard events."""
        if self._stop_event.is_set():
            return
        self._emit({
            "type": "keyboard",
            "data": key_to_string(key),
        })

    def _handle_click(
        self,
        x: int,
        y: int,
        button: mouse.Button,
        pressed: bool,
    ) -> None:
        if self._stop_event.is_set():
            return
        state = "pressed" if pressed else "released"
        self._emit({
            "type": "mouse",
            "data": f"{button.name}-{state}",
            "position": f"{x},{y}",
        })

    def _handle_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if self._stop_event.is_set():
            return
        self._emit({
            "type": "mouse",
            "data": "scroll",
            "delta": f"{dx},{dy}",
            "position": f"{x},{y}",
        })


__all__ = ["InputLogger", "key_to_string"]
