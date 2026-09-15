"""Relevance scoring: rank feed items by how likely they are to point at a
business opportunity a software-engineer-with-a-day-job could act on —
funding programs, procurement, policy shifts creating demand, and signals
of where consulting/contract/product demand is forming.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.fetch import Item

# Weighted keyword groups. Higher weight = stronger signal of an actionable
# opportunity rather than generic economic news.
KEYWORD_WEIGHTS: dict[str, int] = {
    # Funding / money on the table
    r"\bgrant(s)?\b": 5,
    r"\bfunding\b": 4,
    r"\bSR&ED\b": 6,
    r"\bIRAP\b": 6,
    r"\bsubsid(y|ies)\b": 4,
    r"\btax credit(s)?\b": 4,
    r"\bprocurement\b": 5,
    r"\btender(s)?\b": 5,
    r"\bRFP\b": 6,
    r"\bcontract award(s|ed)?\b": 4,
    r"\binvestment\b": 2,
    r"\bventure capital\b": 3,
    r"\bseries [a-e]\b": 3,
    # Policy shifts that create demand
    r"\bdigitiz(e|ation|ing)\b": 5,
    r"\bautomation\b": 4,
    r"\bAI adoption\b": 5,
    r"\bartificial intelligence\b": 3,
    r"\bcybersecurity\b": 4,
    r"\bregulat(ion|ory|ions)\b": 3,
    r"\bcompliance\b": 3,
    r"\bmodernization\b": 4,
    r"\bskills shortage\b": 4,
    r"\blabou?r shortage\b": 4,
    r"\bsmall business\b": 3,
    r"\bSME(s)?\b": 3,
    r"\bstartup(s)?\b": 3,
    r"\bincubator\b": 3,
    r"\baccelerator\b": 3,
    r"\bsoftware\b": 2,
    r"\btechnology sector\b": 2,
    r"\bfintech\b": 3,
    r"\bcleantech\b": 3,
    r"\bsupply chain\b": 2,
    r"\bTariff(s)?\b": 3,
    r"\btrade war\b": 3,
    r"\bnearshoring\b": 4,
    r"\breshoring\b": 4,
    r"\bimmigration\b": 2,
    r"\bhousing\b": 1,
    r"\binterest rate(s)?\b": 2,
    r"\bbudget\b": 3,
    r"\beconomic outlook\b": 3,
    r"\bwhite paper\b": 4,
    r"\bconsulting\b": 3,
    r"\bToronto\b": 3,
    r"\bOntario\b": 2,
}

def _clean_label(pattern: str) -> str:
    label = re.sub(r"\\b|\(|\)|\?|\$", "", pattern)
    return label.replace(r"\s+", " ").strip()


_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), weight, _clean_label(pattern))
    for pattern, weight in KEYWORD_WEIGHTS.items()
]


@dataclass
class ScoredItem:
    item: Item
    score: int
    matched_keywords: list[str]


def score_item(item: Item) -> ScoredItem:
    text = f"{item.title} {item.summary}"
    score = 0
    matched: list[str] = []
    for pattern, weight, label in _COMPILED:
        if pattern.search(text):
            score += weight
            matched.append(label)
    return ScoredItem(item=item, score=score, matched_keywords=matched)


def score_items(items: list[Item]) -> list[ScoredItem]:
    return [score_item(item) for item in items]
