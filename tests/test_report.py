from datetime import datetime, timedelta, timezone

from pipeline.fetch import FetchResult, Item
from pipeline.report import build_report, window_since
from pipeline.score import ScoredItem


def _scored(title: str, days_ago: int, score: int = 5, link: str = "https://example.com/x") -> ScoredItem:
    item = Item(
        title=title,
        link=link,
        summary="Some grant funding announcement.",
        published=datetime.now(tz=timezone.utc) - timedelta(days=days_ago),
        source="Test Source",
        category="government",
    )
    return ScoredItem(item=item, score=score, matched_keywords=["grant"])


def test_old_items_excluded_from_daily_window():
    fresh = _scored("Fresh item", days_ago=0)
    stale = _scored("Stale item", days_ago=10, link="https://example.com/y")
    result = FetchResult(items=[], ok_sources=["Test Source"], failed_sources=[])
    report = build_report([fresh, stale], result, "Daily", window_since("daily"))
    assert "Fresh item" in report
    assert "Stale item" not in report


def test_duplicate_links_deduped():
    a = _scored("Item A", days_ago=0, link="https://example.com/dupe")
    b = _scored("Item A again", days_ago=0, link="https://example.com/dupe")
    result = FetchResult(items=[], ok_sources=[], failed_sources=[])
    report = build_report([a, b], result, "Daily", window_since("daily"))
    assert report.count("https://example.com/dupe") == 1


def test_failed_sources_listed_in_health_section():
    result = FetchResult(items=[], ok_sources=[], failed_sources=[("Broken Feed", "HTTP 404")])
    report = build_report([], result, "Daily", window_since("daily"))
    assert "Broken Feed" in report
    assert "HTTP 404" in report
