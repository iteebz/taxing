from decimal import Decimal

from src.core.depreciation import (
    calc_book_value,
    calc_cumulative_depreciation,
    calc_depreciation,
    depreciation_schedule,
)
from src.core.models import Asset


def test_calc_depreciation_pc():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
        depreciation_method="PC",
    )
    assert calc_depreciation(asset, 25) == Decimal("200")


def test_calc_depreciation_dv():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
        depreciation_method="DV",
    )
    dep_fy25 = calc_depreciation(asset, 25)
    dep_fy26 = calc_depreciation(asset, 26)
    assert dep_fy25 == Decimal("400")
    assert dep_fy26 == Decimal("240")


def test_calc_depreciation_before_purchase():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
    )
    assert calc_depreciation(asset, 24) == Decimal("0")


def test_cumulative_depreciation_full_life():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
    )
    assert calc_cumulative_depreciation(asset, 25, 29) == Decimal("1000")


def test_book_value_trajectory():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
    )
    assert calc_book_value(asset, 25) == Decimal("800")
    assert calc_book_value(asset, 29) == Decimal("0")


def test_depreciation_schedule():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Decimal("1000"),
        life_years=5,
    )
    schedule = depreciation_schedule(asset, 29)
    assert len(schedule) == 5
    assert all(v == Decimal("200") for v in schedule.values())
