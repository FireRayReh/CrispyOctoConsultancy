"""Fetch and normalize items from the configured RSS/Atom sources."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import feedparser
import yaml


@dataclass
class Item:
    title: str
    link: str
    summary: str
    published: datetime
    source: str
    category: str


@dataclass
class FetchResult:
    items: list[Item] = field(default_factory=list)
    ok_sources: list[str] = field(default_factory=list)
    failed_sources: list[tuple[str, str]] = field(default_factory=list)  # (name, reason)


def load_sources(path: str = "sources.yaml") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("sources", [])


def _parse_published(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        value = getattr(entry, key, None)
        if value:
            return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
    return datetime.now(tz=timezone.utc)


def fetch_source(source: dict, timeout: int = 20) -> tuple[list[Item], str | None]:
    """Fetch a single feed. Returns (items, error) — error is None on success.

    Never raises: a malformed or unreachable feed is reported as a failure
    for the caller to log, not a crash that takes down the whole run.
    """
    name = source["name"]
    category = source.get("category", "uncategorized")
    url = source["url"]

    try:
        parsed = feedparser.parse(url, request_headers={"User-Agent": "canada-econ-dashboard/1.0"})
    except Exception as exc:  # network/parse failures shouldn't kill the run
        return [], f"exception: {exc}"

    if getattr(parsed, "bozo", False) and not parsed.entries:
        reason = getattr(parsed, "bozo_exception", "unknown parse error")
        return [], f"parse error: {reason}"

    status = getattr(parsed, "status", None)
    if status and status >= 400:
        return [], f"HTTP {status}"

    if not parsed.entries:
        return [], "no entries returned"

    items = [
        Item(
            title=getattr(entry, "title", "(untitled)").strip(),
            link=getattr(entry, "link", ""),
            summary=getattr(entry, "summary", "").strip(),
            published=_parse_published(entry),
            source=name,
            category=category,
        )
        for entry in parsed.entries
    ]
    return items, None


def fetch_all(sources: list[dict]) -> FetchResult:
    result = FetchResult()
    for source in sources:
        items, error = fetch_source(source)
        if error:
            result.failed_sources.append((source["name"], error))
        else:
            result.ok_sources.append(source["name"])
            result.items.extend(items)
    return result
