from decimal import Decimal

from src.core.models import AUD, Holding, Money


def test_current_value():
    h = Holding(
        ticker="ASX:VAS",
        units=Decimal("50"),
        cost_basis=Money(Decimal("2500"), AUD),
        current_price=Money(Decimal("100"), AUD),
    )
    assert h.current_value == Money(Decimal("5000"), AUD)


def test_unrealized_gain_positive():
    h = Holding(
        ticker="ASX:VGS",
        units=Decimal("200"),
        cost_basis=Money(Decimal("10000"), AUD),
        current_price=Money(Decimal("60"), AUD),
    )
    assert h.unrealized_gain == Money(Decimal("2000"), AUD)


def test_unrealized_gain_negative():
    h = Holding(
        ticker="ASX:NDQ",
        units=Decimal("100"),
        cost_basis=Money(Decimal("8000"), AUD),
        current_price=Money(Decimal("70"), AUD),
    )
    assert h.unrealized_gain == Money(Decimal("-1000"), AUD)


def test_decimal_precision():
    h = Holding(
        ticker="ASX:BHP",
        units=Decimal("123.456"),
        cost_basis=Money(Decimal("12345.67"), AUD),
        current_price=Money(Decimal("45.6789"), AUD),
    )
    expected_value = Decimal("123.456") * Decimal("45.6789")
    assert h.current_value == Money(expected_value, AUD)
