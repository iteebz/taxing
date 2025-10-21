from datetime import date
from decimal import Decimal

from src.core.models import Gain, Trade
from src.core.trades import process_trades
from src.io import from_csv, to_csv


def test_gains_roundtrip(tmp_path):
    """Verify gains can be written to and read from CSV without loss."""
    trades = [
        Trade(
            date=date(2023, 1, 1),
            code="ASX:BHP",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(10),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 8, 1),
            code="ASX:BHP",
            action="sell",
            units=Decimal(100),
            price=Decimal(20),
            fee=Decimal(10),
            individual="tyson",
        ),
    ]

    gains = process_trades(trades)
    csv_path = tmp_path / "gains.csv"

    to_csv(gains, csv_path)
    loaded_gains = from_csv(csv_path, Gain)

    assert len(loaded_gains) == len(gains)
    for orig, loaded in zip(gains, loaded_gains, strict=False):
        assert orig.fy == loaded.fy
        assert orig.raw_profit == loaded.raw_profit
        assert orig.taxable_gain == loaded.taxable_gain


def test_gains_multi_ticker():
    """Test complex scenario: multiple tickers, loss harvesting, discount eligibility."""
    trades = [
        Trade(
            date=date(2022, 1, 1),
            code="ASX:SYI",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(5),
            individual="tyson",
        ),
        Trade(
            date=date(2023, 1, 1),
            code="ASX:NDQ",
            action="buy",
            units=Decimal(50),
            price=Decimal(20),
            fee=Decimal(5),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 1, 1),
            code="ASX:SYI",
            action="sell",
            units=Decimal(100),
            price=Decimal(12),
            fee=Decimal(5),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 1, 1),
            code="ASX:NDQ",
            action="sell",
            units=Decimal(50),
            price=Decimal(18),
            fee=Decimal(5),
            individual="tyson",
        ),
    ]

    gains = process_trades(trades)

    assert len(gains) == 2
    assert all(g.fy == 2024 for g in gains)

    profit_amts = sorted([g.raw_profit for g in gains])
    assert profit_amts == [Decimal(-110), Decimal(190)]
