from decimal import Decimal

from src.core.depreciation import (
    calc_book_value,
    calc_cumulative_depreciation,
    calc_depreciation,
    depreciation_schedule,
)
from src.core.models import AUD, Asset, Money


def test_calc_depreciation_pc():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
        depreciation_method="PC",
    )
    assert calc_depreciation(asset, 25) == Money(Decimal("200"), AUD)


def test_calc_depreciation_dv():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
        depreciation_method="DV",
    )
    dep_fy25 = calc_depreciation(asset, 25)
    dep_fy26 = calc_depreciation(asset, 26)
    assert dep_fy25 == Money(Decimal("400"), AUD)
    assert dep_fy26 == Money(Decimal("240"), AUD)


def test_calc_depreciation_before_purchase():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    assert calc_depreciation(asset, 24) == Money(Decimal("0"), AUD)


def test_cumulative_depreciation_full_life():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    assert calc_cumulative_depreciation(asset, 25, 29) == Money(Decimal("1000"), AUD)


def test_book_value_trajectory():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    assert calc_book_value(asset, 25) == Money(Decimal("800"), AUD)
    assert calc_book_value(asset, 29) == Money(Decimal("0"), AUD)


def test_depreciation_schedule():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    schedule = depreciation_schedule(asset, 29)
    assert len(schedule) == 5
    assert all(v == Money(Decimal("200"), AUD) for v in schedule.values())
