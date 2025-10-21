from decimal import Decimal

from src.core.models import PropertyExpense
from src.core.property import aggregate_expenses


def test_aggregate_single_category():
    expenses = [
        PropertyExpense("rent", Decimal("2000")),
        PropertyExpense("rent", Decimal("2000")),
    ]
    result = aggregate_expenses(expenses)
    assert result.rent == Decimal("4000")
    assert result.total == Decimal("4000")


def test_aggregate_all_categories():
    expenses = [
        PropertyExpense("rent", Decimal("2000")),
        PropertyExpense("water", Decimal("200")),
        PropertyExpense("council", Decimal("400")),
        PropertyExpense("strata", Decimal("300")),
    ]
    result = aggregate_expenses(expenses)
    assert result.total == Decimal("2900")


def test_aggregate_unknown_category_ignored():
    expenses = [
        PropertyExpense("rent", Decimal("2000")),
        PropertyExpense("unknown", Decimal("500")),
    ]
    result = aggregate_expenses(expenses)
    assert result.rent == Decimal("2000")
    assert result.total == Decimal("2000")
