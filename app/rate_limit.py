"""Простейший rate limiter в памяти — без Redis, для одного инстанса.

Для лендинга с небольшим трафиком этого достаточно: ограничиваем, сколько
заявок может отправить один IP за окно времени. Если проект вырастет до
нескольких инстансов за балансировщиком, нужно будет вынести состояние в
Redis — это отдельно отмечено в README.
"""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self.window_seconds

        hits = self._hits[key]
        # Убираем устаревшие попадания вместо хранения их вечно —
        # иначе память будет расти неограниченно для активных IP.
        hits[:] = [t for t in hits if t > window_start]

        if len(hits) >= self.max_requests:
            return False

        hits.append(now)
        return True
