"""Read-only public GitHub API access. Upstream content is data, never code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .jsonutil import strict_loads, utcnow

REPOSITORY = "crewAIInc/crewAI"
API_ROOT = "https://api.github.com/repos/" + REPOSITORY
MAX_BYTES = 8 * 1024 * 1024
MAX_PAGES = 20


class SourceUnavailable(RuntimeError):
    """Coverage is incomplete; the monitor must not advance its baseline."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceUnavailable("Unexpected API redirect; review official source location")


@dataclass(frozen=True)
class Snapshot:
    releases: tuple[dict[str, Any], ...]
    advisories: tuple[dict[str, Any], ...]
    checked_at: str


class OfficialGitHubClient:
    def __init__(self, *, timeout: float = 20, token: str | None = None):
        self.timeout = timeout
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.opener = build_opener(NoRedirects())

    def _page(self, kind: str, page: int) -> list[dict[str, Any]]:
        if kind not in {"releases", "security-advisories"}:
            raise ValueError("Unsupported source")
        url = f"{API_ROOT}/{kind}?per_page=100&page={page}"
        if kind == "security-advisories":
            url += "&state=published"
        headers = {"Accept": "application/vnd.github+json",
                   "User-Agent": "Harmony360-Change-Watch/0.1",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            with self.opener.open(Request(url, headers=headers), timeout=self.timeout) as response:
                if urlparse(response.url).hostname != "api.github.com":
                    raise SourceUnavailable("Unexpected API response host")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise SourceUnavailable("Official API response exceeded size limit")
                value = strict_loads(raw)
        except HTTPError as exc:
            # Do not expose tokens, request headers, or upstream error bodies.
            raise SourceUnavailable(f"Official {kind} API returned HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise SourceUnavailable(f"Official {kind} API could not be read ({type(exc).__name__})") from None
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise SourceUnavailable("Unexpected official API response shape")
        return value

    def _all(self, kind: str) -> tuple[dict[str, Any], ...]:
        records = []
        for page in range(1, MAX_PAGES + 1):
            rows = self._page(kind, page)
            records.extend(rows)
            if len(rows) < 100:
                return tuple(records)
        raise SourceUnavailable("Official API pagination exceeded limit; coverage incomplete")

    def fetch(self) -> Snapshot:
        # Both feeds must finish. A denied advisory request is not an empty feed.
        releases = self._all("releases")
        advisories = self._all("security-advisories")
        return Snapshot(releases, advisories, utcnow())

