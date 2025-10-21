from datetime import date
from decimal import Decimal

from src.io.converters import anz, beem, cba, stake_activity, stake_dividend, wise


def test_anz(sample_anz_row):
    txn = anz(sample_anz_row)
    assert txn.date == date(2024, 10, 1)
    assert txn.amount == Decimal("100.50")
    assert txn.description == "woolworths supermarket"
    assert txn.bank == "anz"
    assert txn.individual == "tyson"


def test_cba(sample_cba_row):
    txn = cba(sample_cba_row)
    assert txn.date == date(2024, 10, 2)
    assert txn.amount == Decimal("-50.25")
    assert txn.description == "amazon purchase"
    assert txn.bank == "cba"
    assert txn.individual == "janice"


def test_beem_received(sample_beem_row):
    txn = beem(sample_beem_row, "tysonchan")
    assert txn.date == date(2024, 10, 3)
    assert txn.amount == Decimal("250.00")
    assert "from tyson" in txn.description
    assert "dinner split" in txn.description
    assert txn.bank == "beem"


def test_beem_sent(sample_beem_row):
    sample_beem_row["recipient"] = "tyson"
    sample_beem_row["payer"] = "tysonchan"
    txn = beem(sample_beem_row, "tysonchan")
    assert txn.amount == Decimal("-250.00")
    assert "to tyson" in txn.description


def test_wise_out(sample_wise_row):
    txn = wise(sample_wise_row)
    assert txn.date == date(2024, 10, 4)
    assert txn.amount == Decimal("-196.30")
    assert "janice quach" in txn.description
    assert txn.bank == "wise"


def test_wise_in(sample_wise_row):
    sample_wise_row["direction"] = "in"
    txn = wise(sample_wise_row)
    assert txn.amount == Decimal("196.30")
    assert "deposit" in txn.description


def test_wise_cancelled(sample_wise_row):
    sample_wise_row["direction"] = "cancelled"
    txn = wise(sample_wise_row)
    assert txn.amount == Decimal("0")
    assert "cancelled" in txn.description


def test_stake_activity_sell():
    row = {
        "Trade Date": "2025-08-06",
        "Symbol": "PLTR",
        "Side": "Sell",
        "Units": "-5",
        "Avg. Price": "179.3",
        "Fees": "0",
        "Currency": "USD",
        "AUD/USD rate": "$1.538",
        "individual": "tyson",
    }
    trade = stake_activity(row)
    assert trade.date == date(2025, 8, 6)
    assert trade.code == "PLTR"
    assert trade.action == "sell"
    assert trade.units == Decimal("5")
    assert trade.price == Decimal("179.3") * Decimal("1.538")
    assert trade.fee == Decimal("0")


def test_stake_activity_buy():
    row = {
        "Trade Date": "2025-08-01",
        "Symbol": "MSFT",
        "Side": "Buy",
        "Units": "10",
        "Avg. Price": "150.00",
        "Fees": "5.00",
        "Currency": "USD",
        "AUD/USD rate": "1.538",
        "individual": "tyson",
    }
    trade = stake_activity(row)
    assert trade.action == "buy"
    assert trade.units == Decimal("10")
    assert trade.fee == Decimal("5.00") * Decimal("1.538")


def test_stake_dividend():
    row = {
        "Payment Date": "2025-07-03",
        "Symbol": "NVDA",
        "Net Amount": "1.03",
        "Currency": "USD",
        "AUD/USD rate": "1.522355",
        "individual": "tyson",
    }
    txn = stake_dividend(row)
    assert txn.date == date(2025, 7, 3)
    assert txn.amount == Decimal("1.03") * Decimal("1.522355")
    assert "dividend nvda" in txn.description
    assert txn.bank == "stake"


def test_sanitize_desc(sample_anz_row):
    sample_anz_row["description_raw"] = 'TEST-DESC "with" quotes'
    txn = anz(sample_anz_row)
    assert txn.description == "test desc with quotes"
