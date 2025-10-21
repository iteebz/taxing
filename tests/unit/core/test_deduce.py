from datetime import date
from decimal import Decimal

import pytest

from src.core.deduce import deduce
from src.core.models import AUD, Money, Transaction


@pytest.fixture
def sample_txns():
    return [
        Transaction(
            date=date(2024, 10, 1),
            amount=Money(Decimal("100.00"), AUD),
            description="WOOLWORTHS",
            source_bank="anz",
            source_person="tyson",
            category={"groceries"},
        ),
        Transaction(
            date=date(2024, 10, 2),
            amount=Money(Decimal("50.00"), AUD),
            description="COLES",
            source_bank="anz",
            source_person="tyson",
            category={"groceries"},
        ),
        Transaction(
            date=date(2024, 10, 3),
            amount=Money(Decimal("200.00"), AUD),
            description="HOME OFFICE DEPOT",
            source_bank="anz",
            source_person="tyson",
            category={"home_office"},
        ),
    ]


@pytest.fixture
def sample_weights():
    return {
        "home_office": 0.8,
        "groceries": 0.05,
    }


def test_single_category(sample_txns, sample_weights):
    deductions = deduce(sample_txns[:1], sample_weights)
    assert deductions["groceries"] == Money(Decimal("5.00"), AUD)


def test_multiple_txns_same_category(sample_txns, sample_weights):
    deductions = deduce(sample_txns[:2], sample_weights)
    assert deductions["groceries"] == Money(Decimal("7.50"), AUD)


def test_multiple_categories(sample_txns, sample_weights):
    deductions = deduce(sample_txns, sample_weights)
    assert deductions["groceries"] == Money(Decimal("7.50"), AUD)
    assert deductions["home_office"] == Money(Decimal("160.00"), AUD)


def test_missing_weight_defaults_to_zero(sample_txns):
    weights = {}
    deductions = deduce(sample_txns, weights)
    assert deductions["groceries"] == Money(Decimal("0.00"), AUD)


def test_empty_transactions():
    deductions = deduce([], {})
    assert deductions == {}


def test_txn_no_category(sample_weights):
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="RANDOM",
        source_bank="anz",
        source_person="tyson",
        category=None,
    )
    deductions = deduce([txn], sample_weights)
    assert deductions == {}


def test_multiple_categories_per_txn(sample_weights):
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="OFFICE GROCERIES",
        source_bank="anz",
        source_person="tyson",
        category={"groceries", "home_office"},
    )
    deductions = deduce([txn], sample_weights)
    assert deductions["groceries"] == Money(Decimal("5.00"), AUD)
    assert deductions["home_office"] == Money(Decimal("80.00"), AUD)


def test_preserves_currency():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="TEST",
        source_bank="anz",
        source_person="tyson",
        category={"groceries"},
    )
    deductions = deduce([txn], {"groceries": 0.5})
    assert deductions["groceries"].currency == AUD
