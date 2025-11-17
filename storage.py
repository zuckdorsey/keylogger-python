"""Local JSON logging helpers for recorded input events."""
from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Iterable
import json
import logging

from config import AppConfig

LOGGER = logging.getLogger(__name__)


class LocalJSONLogger:
    """Append events to a JSON lines file for auditing."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.path: Path = self.config.log_directory_path / "events.jsonl"
        self._lock = Lock()

    def append(self, event: dict) -> None:
        """Append an event as a JSON line."""
        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        LOGGER.debug("Event appended to %s", self.path)

    def read_recent(self, limit: int = 100) -> Iterable[dict]:
        """Read the tail of the log file for quick inspection."""
        if not self.path.exists():
            return []
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:]
        return [json.loads(line) for line in tail]


__all__ = ["LocalJSONLogger"]
