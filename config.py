"""Configuration management utilities for the Personal Input Tracker."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List
import json
import logging

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "webhook_url": "http://127.0.0.1:8000/api/input",
    "send_interval_seconds": 5,
    "batch_size": 25,
    "log_dir": "logs",
    "enable_screenshots": False,
    "screenshot_interval_seconds": 120,
    "debug_mode": False,
    "tray_enabled": True,
    "pending_cache_file": "pending_events.jsonl",
    "screenshot_format": "png",
    "sensitive_title_keywords": ["password", "login", "auth", "credential"],
    "ethics_acknowledged": False,
}


@dataclass
class AppConfig:
    """Dataclass wrapper for user configuration."""

    webhook_url: str = DEFAULT_CONFIG["webhook_url"]
    send_interval_seconds: int = DEFAULT_CONFIG["send_interval_seconds"]
    batch_size: int = DEFAULT_CONFIG["batch_size"]
    log_dir: str = DEFAULT_CONFIG["log_dir"]
    enable_screenshots: bool = DEFAULT_CONFIG["enable_screenshots"]
    screenshot_interval_seconds: int = DEFAULT_CONFIG["screenshot_interval_seconds"]
    debug_mode: bool = DEFAULT_CONFIG["debug_mode"]
    tray_enabled: bool = DEFAULT_CONFIG["tray_enabled"]
    pending_cache_file: str = DEFAULT_CONFIG["pending_cache_file"]
    screenshot_format: str = DEFAULT_CONFIG["screenshot_format"]
    sensitive_title_keywords: List[str] = field(
        default_factory=lambda: list(DEFAULT_CONFIG["sensitive_title_keywords"])
    )
    ethics_acknowledged: bool = DEFAULT_CONFIG["ethics_acknowledged"]

    @property
    def log_directory_path(self) -> Path:
        """Return Path object for log directory and ensure it exists."""
        path = Path(self.log_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def pending_cache_path(self) -> Path:
        """Return Path to pending cache file within log directory."""
        return self.log_directory_path / self.pending_cache_file

    @property
    def config_path(self) -> Path:
        return Path("config.json")


class ConfigManager:
    """Load and persist configuration from disk."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("config.json")
        self.config = AppConfig()

    def load(self) -> AppConfig:
        """Load the config file, falling back to defaults."""
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                merged = {**DEFAULT_CONFIG, **raw}
                self.config = AppConfig(**merged)
                LOGGER.debug("Loaded configuration from %s", self.path)
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.exception("Failed to load config; using defaults: %s", exc)
                self.config = AppConfig()
        else:
            LOGGER.info("Config file missing; writing defaults to %s", self.path)
            self.save()
        return self.config

    def save(self) -> None:
        """Persist the current configuration to disk."""
        try:
            serialized = json.dumps(asdict(self.config), indent=2)
            self.path.write_text(serialized, encoding="utf-8")
            LOGGER.debug("Configuration saved to %s", self.path)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Unable to save configuration: %s", exc)


__all__ = ["AppConfig", "ConfigManager", "DEFAULT_CONFIG"]
