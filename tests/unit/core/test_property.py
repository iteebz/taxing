from decimal import Decimal

from src.core.models import AUD, Money, PropertyExpense
from src.core.property import aggregate_expenses


def test_aggregate_single_category():
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
    ]
    result = aggregate_expenses(expenses)
    assert result.rent == Money(Decimal("4000"), AUD)
    assert result.total == Money(Decimal("4000"), AUD)


def test_aggregate_all_categories():
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("water", Money(Decimal("200"), AUD)),
        PropertyExpense("council", Money(Decimal("400"), AUD)),
        PropertyExpense("strata", Money(Decimal("300"), AUD)),
    ]
    result = aggregate_expenses(expenses)
    assert result.total == Money(Decimal("2900"), AUD)


def test_aggregate_unknown_category_ignored():
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("unknown", Money(Decimal("500"), AUD)),
    ]
    result = aggregate_expenses(expenses)
    assert result.rent == Money(Decimal("2000"), AUD)
    assert result.total == Money(Decimal("2000"), AUD)
