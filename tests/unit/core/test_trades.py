from datetime import date
from decimal import Decimal

from src.core.models import Trade
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
            price=Decimal(10),
            fee=Decimal(10),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="BHP",
            action="sell",
            units=Decimal(100),
            price=Decimal(15),
            fee=Decimal(10),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.fy == 2024
    assert result.raw_profit == Decimal(480)


def test_process_trades_loss_harvesting():
    """Prioritize selling at a loss."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="ABC",
            action="buy",
            units=Decimal(100),
            price=Decimal(20),
            fee=Decimal(10),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 2, 1),
            code="ABC",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(10),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="ABC",
            action="sell",
            units=Decimal(100),
            price=Decimal(12),
            fee=Decimal(10),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit < 0


def test_process_trades_cgt_discount():
    """Position held >365 days gets 50% discount."""
    trades = [
        Trade(
            date=date(2023, 1, 1),
            code="XYZ",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(0),
            individual="tyson",
        ),
        Trade(
            date=date(2025, 1, 5),
            code="XYZ",
            action="sell",
            units=Decimal(100),
            price=Decimal(20),
            fee=Decimal(0),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit == Decimal(1000)
    assert result.taxable_gain == Decimal(500)


def test_mixed_tickers_no_cross():
    """Mixed tickers: AAPL and MSFT buys, MSFT sell must not use AAPL buffer."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="AAPL",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(5),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 1, 2),
            code="MSFT",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(5),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="MSFT",
            action="sell",
            units=Decimal(100),
            price=Decimal(15),
            fee=Decimal(5),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit == Decimal(490)
    assert result.fy == 2024


def test_multiple_sells_fifo():
    """Multiple buys and sells of same ticker, verify FIFO per ticker."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="BHP",
            action="buy",
            units=Decimal(100),
            price=Decimal(10),
            fee=Decimal(0),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 1, 2),
            code="BHP",
            action="buy",
            units=Decimal(100),
            price=Decimal(12),
            fee=Decimal(0),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 6, 1),
            code="BHP",
            action="sell",
            units=Decimal(100),
            price=Decimal(15),
            fee=Decimal(0),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.raw_profit == Decimal(500)


def test_process_trades_crypto_ticker():
    """Verify that crypto tickers are processed correctly."""
    trades = [
        Trade(
            date=date(2024, 1, 1),
            code="CRYPTO:BTC",
            action="buy",
            units=Decimal("0.5"),
            price=Decimal("40000"),
            fee=Decimal("10"),
            individual="tyson",
        ),
        Trade(
            date=date(2024, 7, 1),
            code="CRYPTO:BTC",
            action="sell",
            units=Decimal("0.5"),
            price=Decimal("50000"),
            fee=Decimal("15"),
            individual="tyson",
        ),
    ]

    results = process_trades(trades)

    assert len(results) == 1
    result = results[0]
    assert result.fy == 2025  # FY starts July 1
    # (50000 * 0.5 - 40000 * 0.5) - 10 - 15 = 25000 - 20000 - 25 = 4975
    assert result.raw_profit == Decimal("4975")
    # Held for 182 days (not >365), so no CGT discount
    assert result.taxable_gain == Decimal("4975")
