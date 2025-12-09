"""HTTP fetching layer with simple retry logic."""

from __future__ import annotations

import requests


class FetchError(Exception):
    """Raised when fetching a URL fails after retries."""


class Fetcher:
    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        headers: dict | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        # Copy headers so callers can reuse their dict without mutation.
        self.headers = headers.copy() if headers else {}

    def get(self, url: str) -> str:
        last_status: int | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers=self.headers,
                )
            except requests.exceptions.RequestException as exc:
                if attempt == self.max_retries:
                    raise FetchError(f"Failed to fetch {url}: {exc}") from exc
                continue

            last_status = response.status_code

            if 500 <= response.status_code < 600:
                if attempt == self.max_retries:
                    raise FetchError(
                        f"Failed to fetch {url}: received status {response.status_code}"
                    )
                continue

            if 400 <= response.status_code < 500:
                raise FetchError(
                    f"Failed to fetch {url}: received status {response.status_code}"
                )

            return response.text

        raise FetchError(
            f"Failed to fetch {url}: received status {last_status}"
        )
