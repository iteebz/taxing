from datetime import date
from decimal import Decimal

from src.core.metrics import coverage, household_metrics
from src.core.models import Transaction


def test_coverage_all_labeled():
    """Coverage when all transactions are labeled."""
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
            amount=Decimal("5000"),
            description="SALARY",
            bank="anz",
            individual="alice",
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
            amount=Decimal("-100"),
            description="WOOLWORTHS",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("-200"),
            description="UNKNOWN MERCHANT",
            bank="anz",
            individual="alice",
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
            amount=Decimal("-100"),
            description="WOOLWORTHS",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("5000"),
            description="SALARY",
            bank="anz",
            individual="alice",
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
            amount=Decimal("-1000"),
            description="TRANSFER TO BOB",
            bank="anz",
            individual="alice",
            category={"transfers"},
            is_transfer=True,
        ),
        Transaction(
            date=date(2025, 1, 1),
            amount=Decimal("1000"),
            description="TRANSFER FROM ALICE",
            bank="anz",
            individual="bob",
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
            amount=Decimal("-100"),
            description="GROCERIES",
            bank="anz",
            individual="alice",
            category={"groceries"},
        ),
        Transaction(
            date=date(2025, 1, 2),
            amount=Decimal("5000"),
            description="SALARY",
            bank="anz",
            individual="alice",
            category={"income"},
        ),
        Transaction(
            date=date(2025, 1, 3),
            amount=Decimal("-50"),
            description="CAFE",
            bank="cba",
            individual="bob",
            category={"dining"},
        ),
        Transaction(
            date=date(2025, 1, 4),
            amount=Decimal("3000"),
            description="SALARY",
            bank="cba",
            individual="bob",
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
