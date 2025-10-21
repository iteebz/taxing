from datetime import date
from decimal import Decimal

from src.core.models import AUD, Money, Trade
from src.core.trades import process_trades
from src.io import gains_from_csv, gains_to_csv


def test_gains_roundtrip(tmp_path):
    """Verify gains can be written to and read from CSV without loss."""
    trades = [
        Trade(
            date=date(2023, 1, 1),
            code="ASX:BHP",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 8, 1),
            code="ASX:BHP",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(20), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
    ]

    gains = process_trades(trades)
    csv_path = tmp_path / "gains.csv"

    gains_to_csv(gains, csv_path)
    loaded_gains = gains_from_csv(csv_path)

    assert len(loaded_gains) == len(gains)
    for orig, loaded in zip(gains, loaded_gains, strict=False):
        assert orig.fy == loaded.fy
        assert orig.raw_profit.amount == loaded.raw_profit.amount
        assert orig.taxable_gain.amount == loaded.taxable_gain.amount
        assert orig.action == loaded.action


def test_gains_multi_ticker():
    """Test complex scenario: multiple tickers, loss harvesting, discount eligibility."""
    trades = [
        Trade(
            date=date(2022, 1, 1),
            code="ASX:SYI",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2023, 1, 1),
            code="ASX:NDQ",
            action="buy",
            units=Decimal(50),
            price=Money(Decimal(20), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 1, 1),
            code="ASX:SYI",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(12), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 1, 1),
            code="ASX:NDQ",
            action="sell",
            units=Decimal(50),
            price=Money(Decimal(18), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
    ]

    gains = process_trades(trades)

    assert len(gains) == 2
    assert all(g.fy == 2024 for g in gains)
    assert all(g.action in ["discount", "loss"] for g in gains)

    profit_amts = sorted([g.raw_profit.amount for g in gains])
    assert profit_amts == [Decimal(-105), Decimal(195)]
