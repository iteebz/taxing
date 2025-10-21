"""Property expense aggregation tests."""

from decimal import Decimal

from src.core.models import AUD, Money, PropertyExpense
from src.core.property import aggregate_expenses


def test_aggregate_single_category():
    """Aggregate expenses from one category."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("4000"), AUD)
    assert result.water == Money(Decimal("0"), AUD)
    assert result.council == Money(Decimal("0"), AUD)
    assert result.strata == Money(Decimal("0"), AUD)
    assert result.total == Money(Decimal("4000"), AUD)


def test_aggregate_all_categories():
    """Aggregate expenses from all four categories."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("water", Money(Decimal("200"), AUD)),
        PropertyExpense("council", Money(Decimal("400"), AUD)),
        PropertyExpense("strata", Money(Decimal("300"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("2000"), AUD)
    assert result.water == Money(Decimal("200"), AUD)
    assert result.council == Money(Decimal("400"), AUD)
    assert result.strata == Money(Decimal("300"), AUD)
    assert result.total == Money(Decimal("2900"), AUD)


def test_aggregate_multiple_per_category():
    """Multiple entries per category sum correctly."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("1000"), AUD)),
        PropertyExpense("rent", Money(Decimal("1000"), AUD)),
        PropertyExpense("water", Money(Decimal("100"), AUD)),
        PropertyExpense("water", Money(Decimal("100"), AUD)),
        PropertyExpense("council", Money(Decimal("200"), AUD)),
        PropertyExpense("council", Money(Decimal("200"), AUD)),
        PropertyExpense("strata", Money(Decimal("150"), AUD)),
        PropertyExpense("strata", Money(Decimal("150"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("2000"), AUD)
    assert result.water == Money(Decimal("200"), AUD)
    assert result.council == Money(Decimal("400"), AUD)
    assert result.strata == Money(Decimal("300"), AUD)
    assert result.total == Money(Decimal("2900"), AUD)


def test_aggregate_empty_list():
    """Empty expense list returns all zeros."""
    result = aggregate_expenses([])

    assert result.rent == Money(Decimal("0"), AUD)
    assert result.water == Money(Decimal("0"), AUD)
    assert result.council == Money(Decimal("0"), AUD)
    assert result.strata == Money(Decimal("0"), AUD)
    assert result.total == Money(Decimal("0"), AUD)


def test_aggregate_unknown_category():
    """Unknown categories are ignored."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("unknown", Money(Decimal("500"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("2000"), AUD)
    assert result.total == Money(Decimal("2000"), AUD)


def test_aggregate_decimal_precision():
    """Decimal precision preserved through aggregation."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("1234.56"), AUD)),
        PropertyExpense("rent", Money(Decimal("5678.90"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("6913.46"), AUD)


def test_aggregate_zero_amounts():
    """Zero amounts are aggregated correctly."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("0"), AUD)),
        PropertyExpense("rent", Money(Decimal("0"), AUD)),
    ]
    result = aggregate_expenses(expenses)

    assert result.rent == Money(Decimal("0"), AUD)
    assert result.total == Money(Decimal("0"), AUD)
