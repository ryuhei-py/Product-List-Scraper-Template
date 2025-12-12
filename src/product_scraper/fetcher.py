"""HTTP fetching layer with retry logic and optional backoff."""

from __future__ import annotations

import random
import time

import requests


class FetchError(Exception):
    """Raised when fetching a URL fails after retries."""


class Fetcher:
    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        headers: dict | None = None,
        retry_backoff_seconds: float = 0.0,
        retry_backoff_multiplier: float = 2.0,
        retry_jitter_seconds: float = 0.0,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.retry_jitter_seconds = retry_jitter_seconds
        # Copy headers so callers can reuse their dict without mutation.
        self.headers = headers.copy() if headers else {}
        self.session = session or requests.Session()

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code < 600

    def _sleep_backoff(self, attempt: int) -> None:
        if self.retry_backoff_seconds <= 0:
            return
        backoff = self.retry_backoff_seconds * (self.retry_backoff_multiplier ** (attempt - 1))
        if self.retry_jitter_seconds > 0:
            backoff += random.uniform(0, self.retry_jitter_seconds)
        time.sleep(backoff)

    def get(self, url: str) -> str:
        last_status: int | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    headers=self.headers,
                )
            except requests.exceptions.RequestException as exc:
                if attempt == self.max_retries:
                    raise FetchError(f"Failed to fetch {url}: {exc}") from exc
                self._sleep_backoff(attempt)
                continue

            last_status = response.status_code

            if self._should_retry_status(response.status_code):
                if attempt == self.max_retries:
                    raise FetchError(
                        f"Failed to fetch {url}: received status {response.status_code}"
                    )
                self._sleep_backoff(attempt)
                continue

            if 400 <= response.status_code < 500:
                raise FetchError(
                    f"Failed to fetch {url}: received status {response.status_code}"
                )

            return response.text

        raise FetchError(f"Failed to fetch {url}: received status {last_status}")
