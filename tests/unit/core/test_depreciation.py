from decimal import Decimal

from src.core.depreciation import (
    calc_book_value,
    calc_cumulative_depreciation,
    calc_depreciation,
    depreciation_schedule,
)
from src.core.models import AUD, Asset, Money


def test_calc_depreciation_year_one():
    asset = Asset(
        fy=25,
        description="Home office furniture",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    dep = calc_depreciation(asset, 25)
    assert dep == Money(Decimal("200"), AUD)


def test_calc_depreciation_consistent_across_years():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    for fy in range(25, 30):
        dep = calc_depreciation(asset, fy)
        assert dep == Money(Decimal("200"), AUD)


def test_calc_depreciation_before_purchase():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    dep = calc_depreciation(asset, 24)
    assert dep == Money(Decimal("0"), AUD)


def test_calc_cumulative_depreciation_single_year():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    cum = calc_cumulative_depreciation(asset, 25, 25)
    assert cum == Money(Decimal("200"), AUD)


def test_calc_cumulative_depreciation_five_years():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    cum = calc_cumulative_depreciation(asset, 25, 29)
    assert cum == Money(Decimal("1000"), AUD)


def test_calc_cumulative_depreciation_partial_range():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    cum = calc_cumulative_depreciation(asset, 26, 28)
    assert cum == Money(Decimal("600"), AUD)


def test_calc_book_value_at_purchase():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    book = calc_book_value(asset, 25)
    assert book == Money(Decimal("800"), AUD)


def test_calc_book_value_fully_depreciated():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    book = calc_book_value(asset, 29)
    assert book == Money(Decimal("0"), AUD)


def test_depreciation_schedule_five_year_asset():
    asset = Asset(
        fy=25,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    schedule = depreciation_schedule(asset, 29)
    
    assert len(schedule) == 5
    assert all(v == Money(Decimal("200"), AUD) for v in schedule.values())


def test_depreciation_schedule_starts_at_purchase_year():
    asset = Asset(
        fy=26,
        description="Equipment",
        cost=Money(Decimal("1000"), AUD),
        life_years=5,
    )
    schedule = depreciation_schedule(asset, 30)
    
    assert 25 not in schedule
    assert 26 in schedule
    assert 30 in schedule
