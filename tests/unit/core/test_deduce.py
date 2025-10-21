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
            description="OFFICE SUPPLIES",
            source_bank="anz",
            source_person="tyson",
            category={"software"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 2),
            amount=Money(Decimal("50.00"), AUD),
            description="OFFICE SUPPLIES",
            source_bank="anz",
            source_person="tyson",
            category={"software"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 3),
            amount=Money(Decimal("200.00"), AUD),
            description="HOME OFFICE SETUP",
            source_bank="anz",
            source_person="tyson",
            category={"home_office"},
            personal_pct=Decimal("0"),
        ),
    ]


def test_single_category(sample_txns):
    ded_list = deduce(sample_txns[:1], fy=25)
    assert len(ded_list) == 1
    assert ded_list[0].category == "software"
    assert ded_list[0].amount.amount == Decimal("100.00")
    assert ded_list[0].rate == Decimal("1.0")


def test_multiple_txns_same_category(sample_txns):
    ded_list = deduce(sample_txns[:2], fy=25)
    assert len(ded_list) == 1
    assert ded_list[0].category == "software"
    assert ded_list[0].amount.amount == Decimal("150.00")


def test_multiple_categories(sample_txns):
    ded_list = deduce(sample_txns, fy=25)
    assert len(ded_list) == 2
    by_cat = {d.category: d for d in ded_list}
    assert by_cat["software"].amount.amount == Decimal("150.00")
    assert by_cat["home_office"].amount.amount == Decimal("90.00")


def test_empty_transactions():
    ded_list = deduce([], fy=25)
    assert ded_list == []


def test_txn_no_category():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="RANDOM",
        source_bank="anz",
        source_person="tyson",
        category=None,
    )
    ded_list = deduce([txn], fy=25)
    assert ded_list == []


def test_personal_pct_reduces_deduction():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="OFFICE SUPPLIES",
        source_bank="anz",
        source_person="tyson",
        category={"software"},
        personal_pct=Decimal("0.3"),
    )
    ded_list = deduce([txn], fy=25)
    assert len(ded_list) == 1
    assert ded_list[0].amount.amount == Decimal("70.00")


def test_prohibited_category_skipped():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="CLOTHING",
        source_bank="anz",
        source_person="tyson",
        category={"clothing"},
    )
    ded_list = deduce([txn], fy=25)
    assert len(ded_list) == 0


def test_rate_basis_tracked():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="OFFICE",
        source_bank="anz",
        source_person="tyson",
        category={"home_office"},
    )
    ded_list = deduce([txn], fy=25)
    assert ded_list[0].rate_basis == "ATO_DIVISION_63_SIMPLIFIED"
    assert ded_list[0].fy == 25


def test_conservative_mode():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="HOME OFFICE",
        source_bank="anz",
        source_person="tyson",
        category={"home_office"},
    )
    standard = deduce([txn], fy=25, conservative=False)
    conservative = deduce([txn], fy=25, conservative=True)
    assert conservative[0].amount.amount < standard[0].amount.amount


def test_ignores_foreign_currency():
    eur = "EUR"
    aud_txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="OFFICE",
        source_bank="anz",
        source_person="tyson",
        category={"software"},
    )
    eur_txn = Transaction(
        date=date(2024, 10, 2),
        amount=Money(Decimal("100.00"), eur),
        description="FOREIGN",
        source_bank="wise",
        source_person="tyson",
        category={"software"},
    )
    ded_list = deduce([aud_txn, eur_txn], fy=25)
    assert len(ded_list) == 1
    assert ded_list[0].amount.amount == Decimal("100.00")

def test_confidence_filtering():
    high_conf = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="OFFICE",
        source_bank="anz",
        source_person="tyson",
        category={"software"},
        confidence=0.9,
    )
    low_conf = Transaction(
        date=date(2024, 10, 2),
        amount=Money(Decimal("50.00"), AUD),
        description="OFFICE",
        source_bank="anz",
        source_person="tyson",
        category={"software"},
        confidence=0.3,
    )
    ded_list = deduce([high_conf, low_conf], fy=25, min_confidence=0.5)
    assert len(ded_list) == 1
    assert ded_list[0].amount.amount == Decimal("100.00")

def test_weights_override():
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="ELECTRONICS",
        source_bank="anz",
        source_person="tyson",
        category={"electronics"},
    )
    standard = deduce([txn], fy=25)
    assert standard[0].amount.amount == Decimal("80.00")
    
    override = deduce([txn], fy=25, weights={"electronics": 1.0})
    assert override[0].amount.amount == Decimal("100.00")
