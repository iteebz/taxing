from datetime import date
from decimal import Decimal

import pytest

from src.core.models import Money, Transaction


def test_money_creation():
    m = Money(Decimal("100.00"), "AUD")
    assert m.amount == Decimal("100.00")
    assert m.currency == "AUD"


def test_money_immutable():
    m = Money(Decimal("100.00"), "AUD")
    with pytest.raises(AttributeError):
        m.amount = Decimal("200.00")


def test_money_add_same_curr():
    m1 = Money(Decimal("100.00"), "AUD")
    m2 = Money(Decimal("50.00"), "AUD")
    result = m1 + m2
    assert result.amount == Decimal("150.00")
    assert result.currency == "AUD"


def test_money_add_diff_curr_raises():
    m1 = Money(Decimal("100.00"), "AUD")
    m2 = Money(Decimal("50.00"), "USD")
    with pytest.raises(ValueError):
        m1 + m2


def test_money_multiply():
    m = Money(Decimal("100.00"), "AUD")
    result = m * 0.5
    assert result.amount == Decimal("50.00")
    assert result.currency == "AUD"


def test_txn_creation():
    t = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("50.00"), "AUD"),
        description="WOOLWORTHS",
        source_bank="anz",
        source_person="tyson",
    )
    assert t.description == "WOOLWORTHS"
    assert t.category is None
    assert t.is_transfer is False


def test_txn_with_category():
    t = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("50.00"), "AUD"),
        description="WOOLWORTHS",
        source_bank="anz",
        source_person="tyson",
        category={"groceries", "supermarkets"},
    )
    assert "groceries" in t.category


def test_txn_immutable():
    t = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("50.00"), "AUD"),
        description="WOOLWORTHS",
        source_bank="anz",
        source_person="tyson",
    )
    with pytest.raises(AttributeError):
        t.description = "COLES"
