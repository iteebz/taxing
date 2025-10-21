from datetime import date
from decimal import Decimal

from src.core.models import AUD, Money, Trade
from src.core.trades import calc_fy, is_cgt_discount_eligible, process_trades


def test_calc_fy_before_july():
    assert calc_fy(date(2025, 1, 15)) == 2025


def test_calc_fy_after_july():
    assert calc_fy(date(2025, 7, 1)) == 2026


def test_cgt_discount_eligible_over_365_days():
    assert is_cgt_discount_eligible(365) is True


def test_cgt_discount_not_eligible_under_365_days():
    assert is_cgt_discount_eligible(364) is False


def test_process_trades_simple_buy_sell():
    """Buy low, sell high, FIFO matching."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="BHP",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="BHP",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(15), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.fy == 2024
    assert result.raw_profit.amount == Decimal(480)
    assert result.action == "fifo"


def test_process_trades_loss_harvesting():
    """Prioritize selling at a loss."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="ABC",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(20), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 2, 1),
            code="ABC",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="ABC",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(12), AUD),
            fee=Money(Decimal(10), AUD),
            source_person="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.action == "loss"


def test_process_trades_cgt_discount():
    """Position held >365 days gets 50% discount."""
    trades = [
        Trade(
            date=date(2023, 1, 1),
            code="XYZ",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(0), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2025, 1, 5),
            code="XYZ",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(20), AUD),
            fee=Money(Decimal(0), AUD),
            source_person="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit.amount == Decimal(1000)
    assert result.taxable_gain.amount == Decimal(500)
    assert result.action == "discount"


def test_process_trades_mixed_tickers_no_cross_contamination():
    """Mixed tickers: AAPL and MSFT buys, MSFT sell must not use AAPL buffer."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="AAPL",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 1, 2),
            code="MSFT",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="MSFT",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(15), AUD),
            fee=Money(Decimal(5), AUD),
            source_person="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit.amount == Decimal(490)
    assert result.fy == 2024
    assert result.action == "fifo"


def test_process_trades_multiple_sells_per_ticker():
    """Multiple buys and sells of same ticker, verify FIFO per ticker."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="BHP",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(10), AUD),
            fee=Money(Decimal(0), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 1, 2),
            code="BHP",
            action="buy",
            units=Decimal(100),
            price=Money(Decimal(12), AUD),
            fee=Money(Decimal(0), AUD),
            source_person="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="BHP",
            action="sell",
            units=Decimal(100),
            price=Money(Decimal(15), AUD),
            fee=Money(Decimal(0), AUD),
            source_person="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit.amount == Decimal(500)
    assert result.action == "fifo"
