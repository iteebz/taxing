from datetime import date
from decimal import Decimal

from src.core.models import AUD, Council, Money, Property, Rent, Strata, Water


def test_total_rental_income():
    rents = [
        Rent(date=date(2025, 7, 1), amount=Money(Decimal("1000"), AUD), tenant="janice", fy=25),
        Rent(date=date(2025, 8, 1), amount=Money(Decimal("1000"), AUD), tenant="janice", fy=25),
    ]
    prop = Property(
        address="123 Main St",
        owner="you",
        fy=25,
        occupancy_pct=Decimal("0.30"),
        rents=rents,
    )
    assert prop.total_rental_income == Money(Decimal("2000"), AUD)


def test_deductible_expenses_with_occupancy():
    waters = [Water(date=date(2025, 7, 1), amount=Money(Decimal("100"), AUD), fy=25)]
    councils = [Council(date=date(2025, 7, 1), amount=Money(Decimal("200"), AUD), fy=25)]
    stratas = [Strata(date=date(2025, 7, 1), amount=Money(Decimal("150"), AUD), fy=25)]
    prop = Property(
        address="123 Main St",
        owner="you",
        fy=25,
        occupancy_pct=Decimal("0.30"),
        waters=waters,
        councils=councils,
        stratas=stratas,
    )
    assert prop.deductible_expenses == Money(Decimal("135"), AUD)


def test_net_rental_income():
    rents = [
        Rent(date=date(2025, 7, 1), amount=Money(Decimal("2000"), AUD), tenant="janice", fy=25)
    ]
    waters = [Water(date=date(2025, 7, 1), amount=Money(Decimal("100"), AUD), fy=25)]
    councils = [Council(date=date(2025, 7, 1), amount=Money(Decimal("200"), AUD), fy=25)]
    stratas = [Strata(date=date(2025, 7, 1), amount=Money(Decimal("150"), AUD), fy=25)]
    prop = Property(
        address="123 Main St",
        owner="you",
        fy=25,
        occupancy_pct=Decimal("0.30"),
        rents=rents,
        waters=waters,
        councils=councils,
        stratas=stratas,
    )
    assert prop.net_rental_income == Money(Decimal("1865"), AUD)


def test_invalid_occupancy_pct():
    try:
        Property(
            address="123 Main St",
            owner="you",
            fy=25,
            occupancy_pct=Decimal("1.5"),
        )
        raise AssertionError("Should raise ValueError")
    except ValueError as e:
        assert "occupancy_pct" in str(e)
