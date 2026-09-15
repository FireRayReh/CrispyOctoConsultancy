from datetime import datetime, timezone

from pipeline.fetch import Item
from pipeline.score import score_item


def _item(title: str, summary: str = "") -> Item:
    return Item(
        title=title,
        link="https://example.com/a",
        summary=summary,
        published=datetime.now(tz=timezone.utc),
        source="Test Source",
        category="government",
    )


def test_high_signal_item_scores_above_generic_item():
    high = score_item(_item("Federal government opens new SR&ED grant program for AI adoption"))
    low = score_item(_item("Weather forecast calls for rain in Toronto this weekend"))
    assert high.score > low.score


def test_matched_keywords_are_recorded():
    result = score_item(_item("New procurement RFP for cybersecurity modernization"))
    assert result.score > 0
    assert result.matched_keywords


def test_irrelevant_item_scores_zero():
    result = score_item(_item("Local bakery opens new location downtown"))
    assert result.score == 0
