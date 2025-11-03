from datetime import date
from decimal import Decimal

import pytest

from src.core.models import Transaction
from src.core.validate import (
    ValidationError,
    validate,
    validate_fy_boundary,
    validate_no_duplicates,
    validate_unlabeled,
)


@pytest.fixture
def valid_txn():
    return Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(100),
        description="Test transaction",
        bank="cba",
        individual="tyson",
        cats={"expenses"},
    )


def test_fy_boundary_valid():
    txns = [
        Transaction(
            date=date(2024, 7, 1),
            amount=Decimal(100),
            description="Start of FY2025",
            bank="cba",
            individual="tyson",
            cats={"expenses"},
        ),
        Transaction(
            date=date(2025, 6, 30),
            amount=Decimal(200),
            description="End of FY2025",
            bank="cba",
            individual="tyson",
            cats={"expenses"},
        ),
    ]
    validate_fy_boundary(txns, 25)


def test_fy_boundary_before_start():
    txns = [
        Transaction(
            date=date(2024, 6, 30),
            amount=Decimal(100),
            description="Before FY2025",
            bank="cba",
            individual="tyson",
            cats={"expenses"},
        ),
    ]
    with pytest.raises(ValidationError, match="outside FY25 boundary"):
        validate_fy_boundary(txns, 25)


def test_fy_boundary_after_end():
    txns = [
        Transaction(
            date=date(2025, 7, 1),
            amount=Decimal(100),
            description="After FY2025",
            bank="cba",
            individual="tyson",
            cats={"expenses"},
        ),
    ]
    with pytest.raises(ValidationError, match="outside FY25 boundary"):
        validate_fy_boundary(txns, 25)


def test_no_duplicates_valid(valid_txn):
    txns = [valid_txn]
    validate_no_duplicates(txns)


def test_no_duplicates_exact_match():
    txn1 = Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(100),
        description="Same transaction",
        bank="cba",
        individual="tyson",
        cats={"expenses"},
    )
    txn2 = Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(100),
        description="Same transaction",
        bank="anz",
        individual="tyson",
        cats={"expenses"},
    )
    with pytest.raises(ValidationError, match="Duplicate transaction"):
        validate_no_duplicates([txn1, txn2])


def test_no_duplicates_different_amount():
    txn1 = Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(100),
        description="Transaction",
        bank="cba",
        individual="tyson",
        cats={"expenses"},
    )
    txn2 = Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(101),
        description="Transaction",
        bank="cba",
        individual="tyson",
        cats={"expenses"},
    )
    validate_no_duplicates([txn1, txn2])


def test_unlabeled_valid(valid_txn):
    validate_unlabeled([valid_txn])


def test_unlabeled_missing_category():
    txn = Transaction(
        date=date(2024, 9, 15),
        amount=Decimal(100),
        description="Unlabeled",
        bank="cba",
        individual="tyson",
        cats=None,
    )
    with pytest.raises(ValidationError, match="unlabeled transactions"):
        validate_unlabeled([txn])


def test_full_suite(valid_txn):
    validate([valid_txn], 25)


def test_fails_on_boundary():
    txn = Transaction(
        date=date(2025, 7, 1),
        amount=Decimal(100),
        description="Out of bounds",
        bank="cba",
        individual="tyson",
        cats={"expenses"},
    )
    with pytest.raises(ValidationError, match="FY25"):
        validate([txn], 25)
