#!/usr/bin/env python3
"""
Rate-limited HTTP helpers for world-cup data collection scripts.

Policy: minimum 1 second between outbound requests.
See docs/data-collection-policy.md and .cursor/rules/world-cup-data-collection.mdc.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Mapping

# Project-wide minimum; do not lower without updating data-collection-policy.md
MIN_REQUEST_INTERVAL_SEC = 1.0
DEFAULT_USER_AGENT = "world-cup-kb-collector/1.0 (+local research; rate-limited)"


class RateLimitedFetcher:
    """Serial HTTP client that enforces a minimum gap between requests."""

    def __init__(
        self,
        min_interval_sec: float = MIN_REQUEST_INTERVAL_SEC,
        timeout_sec: float = 30.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        if min_interval_sec < MIN_REQUEST_INTERVAL_SEC:
            raise ValueError(
                f"min_interval_sec must be >= {MIN_REQUEST_INTERVAL_SEC}, got {min_interval_sec}"
            )
        self.min_interval_sec = min_interval_sec
        self.timeout_sec = timeout_sec
        self.user_agent = user_agent
        self._last_request_at: float | None = None

    def wait_for_slot(self) -> None:
        """Block until the next request slot is allowed."""
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.min_interval_sec - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _mark_request(self) -> None:
        self._last_request_at = time.monotonic()

    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        max_retries: int = 3,
    ) -> bytes:
        """
        GET url with rate limiting and simple retry on 429/503.

        Returns response body bytes. Raises urllib.error.HTTPError on other failures.
        """
        last_err: BaseException | None = None
        for attempt in range(max_retries):
            self.wait_for_slot()
            req_headers = {"User-Agent": self.user_agent}
            if headers:
                req_headers.update(headers)
            request = urllib.request.Request(url, headers=req_headers)
            self._mark_request()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_sec) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (429, 503) and attempt < max_retries - 1:
                    backoff = self.min_interval_sec * (2 ** (attempt + 1))
                    time.sleep(backoff)
                    continue
                raise
            except urllib.error.URLError as e:
                last_err = e
                if attempt < max_retries - 1:
                    time.sleep(self.min_interval_sec * (2 ** (attempt + 1)))
                    continue
                raise
        if last_err:
            raise last_err
        raise RuntimeError("unreachable")

    def get_text(
        self,
        url: str,
        encoding: str = "utf-8",
        *,
        headers: Mapping[str, str] | None = None,
        max_retries: int = 3,
    ) -> str:
        return self.get(url, headers=headers, max_retries=max_retries).decode(
            encoding, errors="replace"
        )


def sleep_between_requests(seconds: float = MIN_REQUEST_INTERVAL_SEC) -> None:
    """Convenience sleep when not using RateLimitedFetcher (e.g. MCP manual pacing)."""
    if seconds < MIN_REQUEST_INTERVAL_SEC:
        seconds = MIN_REQUEST_INTERVAL_SEC
    time.sleep(seconds)
