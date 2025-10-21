from decimal import Decimal

from src.core.metrics import coverage, household_metrics
from src.core.models import AUD, Money, Transaction
from datetime import date


def test_coverage_empty():
    """Coverage with no transactions."""
    result = coverage([])
    assert result["pct_txns"] == 0.0
    assert result["count_labeled"] == 0
    assert result["count_total"] == 0


def test_coverage_all_labeled():
    """Coverage when all transactions are labeled."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("-100"), AUD),
            description="WOOLWORTHS",
            source_bank="anz",
            source_person="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Money(Decimal("5000"), AUD),
            description="SALARY",
            source_bank="anz",
            source_person="alice",
            category={"income"},
        ),
    ]

    result = coverage(txns)
    assert result["pct_txns"] == 100.0
    assert result["count_labeled"] == 2
    assert result["count_total"] == 2
    assert result["pct_debit"] == 100.0
    assert result["pct_credit"] == 100.0


def test_coverage_partial():
    """Coverage with mix of labeled/unlabeled."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("-100"), AUD),
            description="WOOLWORTHS",
            source_bank="anz",
            source_person="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Money(Decimal("-200"), AUD),
            description="UNKNOWN MERCHANT",
            source_bank="anz",
            source_person="alice",
            category=None,
        ),
    ]

    result = coverage(txns)
    assert result["pct_txns"] == 50.0
    assert result["count_labeled"] == 1
    assert result["count_total"] == 2
    assert float(result["pct_debit"]) == 33.33


def test_household_metrics_single_person():
    """Household metrics for single person."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("-100"), AUD),
            description="WOOLWORTHS",
            source_bank="anz",
            source_person="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Money(Decimal("5000"), AUD),
            description="SALARY",
            source_bank="anz",
            source_person="alice",
            category={"income"},
        ),
    ]

    result = household_metrics(txns)
    assert result["persons"] == ["alice"]
    assert result["spending_by_person"]["alice"] == 100.0
    assert result["income_by_person"]["alice"] == 5000.0
    assert result["total_spending"] == 100.0
    assert result["total_income"] == 5000.0


def test_household_metrics_transfers():
    """Household metrics count transfers separately."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("-1000"), AUD),
            description="TRANSFER TO BOB",
            source_bank="anz",
            source_person="alice",
            category={"transfers"},
            is_transfer=True,
        ),
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("1000"), AUD),
            description="TRANSFER FROM ALICE",
            source_bank="anz",
            source_person="bob",
            category=None,
        ),
    ]

    result = household_metrics(txns)
    assert result["total_spending"] == 0.0
    assert result["total_income"] == 1000.0
    assert result["total_transfers"] == 1000.0


def test_household_metrics_multi_person():
    """Household metrics for multiple persons."""
    txns = [
        Transaction(
            date=date(2025, 1, 1),
            amount=Money(Decimal("-100"), AUD),
            description="GROCERIES",
            source_bank="anz",
            source_person="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Money(Decimal("5000"), AUD),
            description="SALARY",
            source_bank="anz",
            source_person="alice",
            category={"income"},
        ),
        Transaction(
            date=date(2025, 1, 3),
            amount=Money(Decimal("-50"), AUD),
            description="CAFE",
            source_bank="cba",
            source_person="bob",
            category={"dining"},
        ),
        Transaction(
            date=date(2025, 1, 4),
            amount=Money(Decimal("3000"), AUD),
            description="SALARY",
            source_bank="cba",
            source_person="bob",
            category={"income"},
        ),
    ]

    result = household_metrics(txns)
    assert sorted(result["persons"]) == ["alice", "bob"]
    assert result["spending_by_person"]["alice"] == 100.0
    assert result["spending_by_person"]["bob"] == 50.0
    assert result["income_by_person"]["alice"] == 5000.0
    assert result["income_by_person"]["bob"] == 3000.0
    assert result["total_spending"] == 150.0
    assert result["total_income"] == 8000.0
