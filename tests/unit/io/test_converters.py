from datetime import date
from decimal import Decimal

from src.core.models import AUD
from src.io.converters import anz, beem, cba, wise


def test_anz_converter(sample_anz_row):
    txn = anz(sample_anz_row)
    assert txn.date == date(2024, 10, 1)
    assert txn.amount.amount == Decimal("100.50")
    assert txn.amount.currency == AUD
    assert txn.description == "woolworths supermarket"
    assert txn.source_bank == "anz"
    assert txn.source_person == "tyson"


def test_cba_converter(sample_cba_row):
    txn = cba(sample_cba_row)
    assert txn.date == date(2024, 10, 2)
    assert txn.amount.amount == Decimal("-50.25")
    assert txn.amount.currency == AUD
    assert txn.description == "amazon purchase"
    assert txn.source_bank == "cba"
    assert txn.source_person == "jaynice"


def test_beem_converter_received(sample_beem_row):
    txn = beem(sample_beem_row, "tysonchan")
    assert txn.date == date(2024, 10, 3)
    assert txn.amount.amount == Decimal("250.00")
    assert txn.amount.currency == AUD
    assert "from alice" in txn.description
    assert "dinner split" in txn.description
    assert txn.source_bank == "beem"


def test_beem_converter_sent(sample_beem_row):
    sample_beem_row["recipient"] = "alice"
    sample_beem_row["payer"] = "tysonchan"
    txn = beem(sample_beem_row, "tysonchan")
    assert txn.amount.amount == Decimal("-250.00")
    assert "to alice" in txn.description


def test_wise_converter_out(sample_wise_row):
    txn = wise(sample_wise_row)
    assert txn.date == date(2024, 10, 4)
    assert txn.amount.amount == Decimal("-302.00")
    assert txn.amount.currency == "USD"
    assert "alice smith" in txn.description
    assert txn.source_bank == "wise"


def test_wise_converter_in(sample_wise_row):
    sample_wise_row["direction"] = "in"
    txn = wise(sample_wise_row)
    assert txn.amount.amount == Decimal("302.00")
    assert "deposit" in txn.description


def test_wise_converter_cancelled(sample_wise_row):
    sample_wise_row["direction"] = "cancelled"
    txn = wise(sample_wise_row)
    assert txn.amount.amount == Decimal("0")
    assert "cancelled" in txn.description


def test_description_sanitization(sample_anz_row):
    sample_anz_row["description_raw"] = 'TEST-DESC "with" quotes'
    txn = anz(sample_anz_row)
    assert txn.description == "test desc with quotes"
