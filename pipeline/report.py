"""Render scored items into a markdown report grouped by category."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pipeline.fetch import FetchResult
from pipeline.score import ScoredItem

CATEGORY_TITLES = {
    "government": "Government & Policy",
    "consulting": "Consulting & Bank White Papers",
    "economic_indicators": "Economic Indicators",
    "startup_tech": "Tech & Startup Ecosystem",
    "uncategorized": "Other",
}

MIN_SCORE = 1  # drop pure noise; everything else is ranked, not filtered hard


def _dedupe(scored: list[ScoredItem]) -> list[ScoredItem]:
    seen: set[str] = set()
    deduped = []
    for s in scored:
        key = s.item.link or s.item.title
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    return deduped


def _within_window(scored: list[ScoredItem], since: datetime) -> list[ScoredItem]:
    return [s for s in scored if s.item.published >= since]


def build_report(
    scored: list[ScoredItem],
    fetch_result: FetchResult,
    window_label: str,
    since: datetime,
    top_n_per_category: int = 8,
) -> str:
    scored = _dedupe(scored)
    scored = _within_window(scored, since)
    scored = [s for s in scored if s.score >= MIN_SCORE]

    by_category: dict[str, list[ScoredItem]] = {}
    for s in scored:
        by_category.setdefault(s.item.category, []).append(s)
    for items in by_category.values():
        items.sort(key=lambda s: (s.score, s.item.published), reverse=True)

    now = datetime.now(tz=timezone.utc)
    lines: list[str] = []
    lines.append(f"# Canada Economic Opportunities — {window_label} Report")
    lines.append("")
    lines.append(f"_Generated {now.strftime('%Y-%m-%d %H:%M UTC')} · window since {since.strftime('%Y-%m-%d')}_")
    lines.append("")
    lines.append(
        "Ranked by keyword relevance (funding, procurement, policy shifts, sector demand). "
        "Every item links to its original source — verify before acting."
    )
    lines.append("")

    if not scored:
        lines.append("No items cleared the relevance/recency bar this run. See Source Health below.")
        lines.append("")

    for category, title in CATEGORY_TITLES.items():
        items = by_category.get(category, [])
        if not items:
            continue
        lines.append(f"## {title}")
        lines.append("")
        for s in items[:top_n_per_category]:
            item = s.item
            date_str = item.published.strftime("%Y-%m-%d")
            lines.append(f"- **[{item.title}]({item.link})** — {item.source}, {date_str} (score: {s.score})")
            if s.matched_keywords:
                lines.append(f"  - Signals: {', '.join(sorted(set(s.matched_keywords)))}")
            snippet = _clean_summary(item.summary)
            if snippet:
                lines.append(f"  - {snippet}")
        lines.append("")

    lines.append("## Source Health")
    lines.append("")
    lines.append(f"- OK: {len(fetch_result.ok_sources)} sources — {', '.join(fetch_result.ok_sources) or 'none'}")
    if fetch_result.failed_sources:
        lines.append(f"- Failed: {len(fetch_result.failed_sources)} sources (fix URLs in `sources.yaml`):")
        for name, reason in fetch_result.failed_sources:
            lines.append(f"  - {name}: {reason}")
    else:
        lines.append("- Failed: none")
    lines.append("")

    return "\n".join(lines)


def _clean_summary(summary: str, max_len: int = 220) -> str:
    import re

    text = re.sub(r"<[^>]+>", "", summary).strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text


def window_since(window: str, now: datetime | None = None) -> datetime:
    now = now or datetime.now(tz=timezone.utc)
    if window == "daily":
        return now - timedelta(days=1)
    if window == "weekly":
        return now - timedelta(days=7)
    raise ValueError(f"unknown window: {window}")
