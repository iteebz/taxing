"""Holding model tests."""

from decimal import Decimal

from src.core.models import AUD, Holding, Money


def test_holding_basic():
    """Create holding and verify properties."""
    h = Holding(
        ticker="ASX:SYI",
        units=Decimal("100"),
        cost_basis=Money(Decimal("5000"), AUD),
        current_price=Money(Decimal("60"), AUD),
    )

    assert h.ticker == "ASX:SYI"
    assert h.units == Decimal("100")
    assert h.cost_basis == Money(Decimal("5000"), AUD)
    assert h.current_price == Money(Decimal("60"), AUD)


def test_holding_current_value():
    """Calculate current value (units × price)."""
    h = Holding(
        ticker="ASX:VAS",
        units=Decimal("50"),
        cost_basis=Money(Decimal("2500"), AUD),
        current_price=Money(Decimal("100"), AUD),
    )

    assert h.current_value == Money(Decimal("5000"), AUD)


def test_holding_unrealized_gain_positive():
    """Unrealized gain when price increased."""
    h = Holding(
        ticker="ASX:VGS",
        units=Decimal("200"),
        cost_basis=Money(Decimal("10000"), AUD),
        current_price=Money(Decimal("60"), AUD),
    )

    assert h.current_value == Money(Decimal("12000"), AUD)
    assert h.unrealized_gain == Money(Decimal("2000"), AUD)


def test_holding_unrealized_gain_negative():
    """Unrealized loss when price decreased."""
    h = Holding(
        ticker="ASX:NDQ",
        units=Decimal("100"),
        cost_basis=Money(Decimal("8000"), AUD),
        current_price=Money(Decimal("70"), AUD),
    )

    assert h.current_value == Money(Decimal("7000"), AUD)
    assert h.unrealized_gain == Money(Decimal("-1000"), AUD)


def test_holding_unrealized_gain_zero():
    """No gain when price unchanged."""
    h = Holding(
        ticker="ASX:ETHI",
        units=Decimal("100"),
        cost_basis=Money(Decimal("5000"), AUD),
        current_price=Money(Decimal("50"), AUD),
    )

    assert h.current_value == Money(Decimal("5000"), AUD)
    assert h.unrealized_gain == Money(Decimal("0"), AUD)


def test_holding_decimal_precision():
    """Preserve decimal precision in calculations."""
    h = Holding(
        ticker="ASX:BHP",
        units=Decimal("123.456"),
        cost_basis=Money(Decimal("12345.67"), AUD),
        current_price=Money(Decimal("45.6789"), AUD),
    )

    expected_value = Decimal("123.456") * Decimal("45.6789")
    assert h.current_value == Money(expected_value, AUD)


def test_holding_fractional_units():
    """Support fractional units (micro-cap ETFs)."""
    h = Holding(
        ticker="ASX:VAS",
        units=Decimal("0.5"),
        cost_basis=Money(Decimal("50"), AUD),
        current_price=Money(Decimal("120"), AUD),
    )

    assert h.current_value == Money(Decimal("60"), AUD)
    assert h.unrealized_gain == Money(Decimal("10"), AUD)


def test_holding_immutable():
    """Holding is immutable (frozen dataclass)."""
    h = Holding(
        ticker="ASX:VAS",
        units=Decimal("100"),
        cost_basis=Money(Decimal("5000"), AUD),
        current_price=Money(Decimal("60"), AUD),
    )

    try:
        h.units = Decimal("200")
        raise AssertionError("Should not allow mutation")
    except (AttributeError, TypeError):
        pass


def test_holding_multiple_tickers():
    """Support various ticker formats."""
    tickers = ["ASX:SYI", "ASX:NDQ", "VAS", "TSLA", "AAPL"]

    for ticker in tickers:
        h = Holding(
            ticker=ticker,
            units=Decimal("100"),
            cost_basis=Money(Decimal("5000"), AUD),
            current_price=Money(Decimal("60"), AUD),
        )
        assert h.ticker == ticker


def test_holding_large_positions():
    """Handle large positions without precision loss."""
    h = Holding(
        ticker="ASX:VAS",
        units=Decimal("100000"),
        cost_basis=Money(Decimal("5000000"), AUD),
        current_price=Money(Decimal("60.5"), AUD),
    )

    assert h.current_value == Money(Decimal("6050000"), AUD)
    assert h.unrealized_gain == Money(Decimal("1050000"), AUD)
