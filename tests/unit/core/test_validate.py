from datetime import date

import pytest

from src.core.models import AUD, Money, Transaction
from src.core.validate import (
    ValidationError,
    validate_no_duplicates,
    validate_transactions,
    validate_unlabeled,
    validate_fy_boundary,
)


@pytest.fixture
def valid_txn():
    return Transaction(
        date=date(2024, 9, 15),
        amount=Money(100, AUD),
        description="Test transaction",
        source_bank="cba",
        source_person="tyson",
        category={"expenses"},
    )


def test_validate_fy_boundary_valid():
    txns = [
        Transaction(
            date=date(2024, 7, 1),
            amount=Money(100, AUD),
            description="Start of FY2025",
            source_bank="cba",
            source_person="tyson",
            category={"expenses"},
        ),
        Transaction(
            date=date(2025, 6, 30),
            amount=Money(200, AUD),
            description="End of FY2025",
            source_bank="cba",
            source_person="tyson",
            category={"expenses"},
        ),
    ]
    validate_fy_boundary(txns, 25)


def test_validate_fy_boundary_before_start():
    txns = [
        Transaction(
            date=date(2024, 6, 30),
            amount=Money(100, AUD),
            description="Before FY2025",
            source_bank="cba",
            source_person="tyson",
            category={"expenses"},
        ),
    ]
    with pytest.raises(ValidationError, match="outside FY25 boundary"):
        validate_fy_boundary(txns, 25)


def test_validate_fy_boundary_after_end():
    txns = [
        Transaction(
            date=date(2025, 7, 1),
            amount=Money(100, AUD),
            description="After FY2025",
            source_bank="cba",
            source_person="tyson",
            category={"expenses"},
        ),
    ]
    with pytest.raises(ValidationError, match="outside FY25 boundary"):
        validate_fy_boundary(txns, 25)


def test_validate_no_duplicates_valid(valid_txn):
    txns = [valid_txn]
    validate_no_duplicates(txns)


def test_validate_no_duplicates_exact_match():
    txn1 = Transaction(
        date=date(2024, 9, 15),
        amount=Money(100, AUD),
        description="Same transaction",
        source_bank="cba",
        source_person="tyson",
        category={"expenses"},
    )
    txn2 = Transaction(
        date=date(2024, 9, 15),
        amount=Money(100, AUD),
        description="Same transaction",
        source_bank="anz",
        source_person="tyson",
        category={"expenses"},
    )
    with pytest.raises(ValidationError, match="Duplicate transaction"):
        validate_no_duplicates([txn1, txn2])


def test_validate_no_duplicates_different_amount():
    txn1 = Transaction(
        date=date(2024, 9, 15),
        amount=Money(100, AUD),
        description="Transaction",
        source_bank="cba",
        source_person="tyson",
        category={"expenses"},
    )
    txn2 = Transaction(
        date=date(2024, 9, 15),
        amount=Money(101, AUD),
        description="Transaction",
        source_bank="cba",
        source_person="tyson",
        category={"expenses"},
    )
    validate_no_duplicates([txn1, txn2])


def test_validate_unlabeled_valid(valid_txn):
    validate_unlabeled([valid_txn])


def test_validate_unlabeled_missing_category():
    txn = Transaction(
        date=date(2024, 9, 15),
        amount=Money(100, AUD),
        description="Unlabeled",
        source_bank="cba",
        source_person="tyson",
        category=None,
    )
    with pytest.raises(ValidationError, match="unlabeled transactions"):
        validate_unlabeled([txn])


def test_validate_transactions_full_suite(valid_txn):
    validate_transactions([valid_txn], 25)


def test_validate_transactions_fails_on_boundary():
    txn = Transaction(
        date=date(2025, 7, 1),
        amount=Money(100, AUD),
        description="Out of bounds",
        source_bank="cba",
        source_person="tyson",
        category={"expenses"},
    )
    with pytest.raises(ValidationError, match="FY25"):
        validate_transactions([txn], 25)
