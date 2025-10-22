from datetime import date
from decimal import Decimal

from src.core.mining import (
    extract_keywords,
    find_similar_labeled,
    mine_suggestions,
    score_suggestions,
)
from src.core.models import Transaction


def test_extract_keywords():
    """Extract keywords from description."""
    assert extract_keywords("WOOLWORTHS SUPERMARKET") == ["woolworths", "supermarket"]
    assert extract_keywords("IGA") == ["iga"]
    assert extract_keywords("XY") == []
    assert extract_keywords("XYZ CAFE MELBOURNE") == ["xyz", "cafe", "melbourne"]
    assert extract_keywords("") == []


def test_find_similar_labeled_empty():
    """Find similar with no labeled txns."""
    txns = []
    result = find_similar_labeled(txns, "WOOLWORTHS")
    assert result == []


def test_find_similar_labeled_basic():
    """Find similar labeled transactions."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("-100"),
            description="WOOLWORTHS NORTH SYDNEY",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("-50"),
            description="COLES BONDI",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
    ]

    result = find_similar_labeled(txns, "WOOLWORTHS SURRY HILLS")
    assert len(result) == 1
    assert "WOOLWORTHS" in result[0].description


def test_mine_suggestions_empty():
    """Mine suggestions with no txns."""
    result = mine_suggestions([])
    assert result == []


def test_mine_suggestions_no_unlabeled():
    """Mine suggestions with no unlabeled txns."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("-100"),
            description="WOOLWORTHS",
            bank="anz",
            individual="alice",
            category={"groceries"},
        )
    ]
    result = mine_suggestions(txns)
    assert result == []


def test_mine_suggestions_basic():
    """Mine suggestions from similar labeled txns."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("-100"),
            description="WOOLWORTHS NORTH SYDNEY",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("-50"),
            description="UNKNOWN WOOLWORTHS STORE",
            bank="anz",
            individual="alice",
            category=None,
        ),
    ]

    result = mine_suggestions(txns)
    assert len(result) > 0
    assert any(s.keyword == "woolworths" and s.category == "groceries" for s in result)


def test_score_suggestions_empty():
    """Score empty suggestions."""
    result = score_suggestions([])
    assert result == []


def test_score_suggestions_generic_words():
    """Generic words are filtered."""
    from src.core.mining import RuleSuggestion

    suggestions = [
        RuleSuggestion(
            keyword="transfer",
            category="transfers",
            evidence=50,
            source="keyword",
            unlabeled_desc="test",
        ),
        RuleSuggestion(
            keyword="WOOLWORTHS",
            category="groceries",
            evidence=30,
            source="keyword",
            unlabeled_desc="test",
        ),
    ]

    result = score_suggestions(suggestions)
    assert len(result) == 1
    assert result[0].keyword == "WOOLWORTHS"


def test_score_suggestions_consensus():
    """Consensus filtering (60% threshold)."""
    from src.core.mining import RuleSuggestion

    suggestions = [
        RuleSuggestion(
            keyword="COFFEE",
            category="dining",
            evidence=70,
            source="keyword",
            unlabeled_desc="",
        ),
        RuleSuggestion(
            keyword="COFFEE",
            category="groceries",
            evidence=30,
            source="keyword",
            unlabeled_desc="",
        ),
    ]

    result = score_suggestions(suggestions)
    assert len(result) == 1
    assert result[0].category == "dining"
    assert result[0].evidence == 70


def test_score_suggestions_sorted_by_evidence():
    """Results sorted by evidence (descending)."""
    from src.core.mining import RuleSuggestion

    suggestions = [
        RuleSuggestion(
            keyword="BREAD",
            category="groceries",
            evidence=20,
            source="keyword",
            unlabeled_desc="",
        ),
        RuleSuggestion(
            keyword="MILK",
            category="groceries",
            evidence=100,
            source="keyword",
            unlabeled_desc="",
        ),
        RuleSuggestion(
            keyword="EGGS",
            category="groceries",
            evidence=50,
            source="keyword",
            unlabeled_desc="",
        ),
    ]

    result = score_suggestions(suggestions)
    assert [s.evidence for s in result] == [100, 50, 20]


def test_mine_suggestions_no_search():
    """Mine without search—orphan txns ignored."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("-100"),
            description="WOOLWORTHS",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("-50"),
            description="UNKNOWN MERCHANT XYZ",
            bank="anz",
            individual="alice",
            category=None,
        ),
    ]

    result = mine_suggestions(txns, use_search=False)
    assert result == []


def test_mine_suggestions_with_search_orphan():
    """Mine with search enabled—orphans searched (mock)."""
    from pathlib import Path
    from unittest.mock import patch

    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("-100"),
            description="WOOLWORTHS",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("-50"),
            description="UNKNOWNMERCHANT",
            bank="anz",
            individual="alice",
            category=None,
        ),
    ]

    cache_path = Path("/tmp/test_cache.json")

    with patch("src.lib.search.search_merchant") as mock_search:
        mock_search.return_value = ["This is an online retail store"]

        result = mine_suggestions(txns, use_search=True, cache_path=cache_path)

        assert len(result) > 0
        assert any(s.source == "search" for s in result)
