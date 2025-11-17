"""Entry point for the Personal Input Tracker & Logger."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple
import logging
import signal
import sys

from config import ConfigManager
from gui import TrackerGUI, open_log_directory
from logger import InputLogger
from screenshot import ScreenshotCapturer
from sender import DataSender
from storage import LocalJSONLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger("tracker.main")


class TrackerApplication:
    """Wire together the logger, storage, sender, and GUI."""

    def __init__(self) -> None:
        self.config = ConfigManager().load()
        self.sender = DataSender(self.config)
        self.local_logger = LocalJSONLogger(self.config)
        self.input_logger = InputLogger(self.config, self._handle_event)
        self.screenshot = ScreenshotCapturer(self.config, self._handle_event)
        self.gui = TrackerGUI(
            self.config,
            start_callback=self.start_tracking,
            stop_callback=self.stop_tracking,
            open_logs_callback=self.open_logs,
            stats_provider=self.get_stats,
        )
        self._register_signal_handlers()

    def _register_signal_handlers(self) -> None:
        def _exit_handler(signum, frame):  # pragma: no cover - user exit
            LOGGER.info("Received signal %s, shutting down", signum)
            self.stop_tracking()
            sys.exit(0)

        signal.signal(signal.SIGINT, _exit_handler)
        signal.signal(signal.SIGTERM, _exit_handler)

    def _handle_event(self, payload: dict) -> None:
        """Forward events to local storage and remote sender."""
        self.local_logger.append(payload)
        self.sender.enqueue(payload)

    def start_tracking(self) -> None:
        LOGGER.info("Starting tracking components")
        self.sender.start()
        self.input_logger.start()
        self.screenshot.start()

    def stop_tracking(self) -> None:
        LOGGER.info("Stopping tracking components")
        self.input_logger.stop()
        self.screenshot.stop()
        self.sender.stop()

    def get_stats(self) -> Tuple[int, int]:
        return self.sender.stats()

    def open_logs(self) -> None:
        open_log_directory(self.config.log_directory_path)

    def run(self) -> None:
        self.gui.open()


def main() -> None:
    app = TrackerApplication()
    app.run()


if __name__ == "__main__":
    main()
