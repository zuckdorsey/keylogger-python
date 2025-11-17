"""Data sending and persistence queue."""
from __future__ import annotations

from queue import Queue, Empty
from threading import Event, Thread
from typing import List, Optional
import json
import logging
import time

import requests

from config import AppConfig
from utils import PendingPayload, chunked

LOGGER = logging.getLogger(__name__)


class DataSender:
    """Background sender that POSTs input batches to a webhook."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.queue: "Queue[dict]" = Queue()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self.sent_count = 0
        self.pending_count = 0
        self.session = requests.Session()
        self._pending_cache = PendingPayload.load_from_file(self.config.pending_cache_path)
        self.pending_count = len(self._pending_cache.data)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="DataSender", daemon=True)
        self._thread.start()
        LOGGER.info("Data sender started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.flush_pending_to_disk()
        LOGGER.info("Data sender stopped")

    def enqueue(self, payload: dict) -> None:
        self.queue.put(payload)
        self.pending_count = self.queue.qsize() + len(self._pending_cache.data)

    def _drain_queue(self) -> List[dict]:
        items: List[dict] = []
        while True:
            try:
                items.append(self.queue.get_nowait())
            except Empty:
                break
        return items

    def _run(self) -> None:
        interval = max(1, self.config.send_interval_seconds)
        while not self._stop_event.is_set():
            time.sleep(interval)
            pending = self._pending_cache.data + self._drain_queue()
            if not pending:
                continue
            success = self._send_batch(pending)
            if success:
                self._pending_cache = PendingPayload([])
                self.pending_count = self.queue.qsize()
                self.config.pending_cache_path.unlink(missing_ok=True)
            else:
                self._pending_cache = PendingPayload(pending)
                self.pending_count = len(pending)
                self.flush_pending_to_disk()

    def _send_batch(self, payloads: List[dict]) -> bool:
        batches = list(chunked(payloads, self.config.batch_size))
        all_success = True
        for chunk in batches:
            try:
                response = self.session.post(
                    self.config.webhook_url,
                    timeout=10,
                    json={"events": chunk},
                )
                if response.status_code >= 300:
                    LOGGER.warning(
                        "Server rejected batch with status %s", response.status_code
                    )
                    all_success = False
                    break
                self.sent_count += len(chunk)
            except requests.RequestException as exc:
                LOGGER.error("Failed to send batch: %s", exc)
                all_success = False
                break
        return all_success

    def flush_pending_to_disk(self) -> None:
        if not self._pending_cache.data:
            return
        try:
            self._pending_cache.dump_to_file(self.config.pending_cache_path)
            LOGGER.info("Persisted %s pending events", len(self._pending_cache.data))
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Unable to persist pending queue: %s", exc)

    def stats(self) -> tuple[int, int]:
        return self.sent_count, self.pending_count + self.queue.qsize()


__all__ = ["DataSender"]
