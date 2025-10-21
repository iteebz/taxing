from decimal import Decimal

from src.core.models import AUD, Individual, Money


def test_allocate_threshold_you_empty_janice_full():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("0"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("30000"), AUD),
    )
    shared_deductions = [Money(Decimal("5000"), AUD), Money(Decimal("3000"), AUD)]

    from src.core.household import allocate_deductions

    your_ded, janice_ded = allocate_deductions(
        yours.income, janice.income, shared_deductions, fy=25
    )

    assert your_ded == Money(Decimal("8000"), AUD)
    assert janice_ded == Money(Decimal("0"), AUD)


def test_allocate_threshold_you_has_buffer_janice_exceeded():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("10000"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("50000"), AUD),
    )
    shared_deductions = [Money(Decimal("5000"), AUD), Money(Decimal("5000"), AUD)]

    from src.core.household import allocate_deductions

    your_ded, janice_ded = allocate_deductions(
        yours.income, janice.income, shared_deductions, fy=25
    )

    your_buffer = Decimal("18200") - Decimal("10000")
    remaining = Decimal("10000") - your_buffer
    assert your_ded == Money(your_buffer, AUD)
    assert janice_ded == Money(remaining, AUD)


def test_allocate_threshold_both_under():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("5000"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("8000"), AUD),
    )
    shared_deductions = [Money(Decimal("3000"), AUD)]

    from src.core.household import allocate_deductions

    your_ded, janice_ded = allocate_deductions(
        yours.income, janice.income, shared_deductions, fy=25
    )

    assert your_ded == Money(Decimal("3000"), AUD)
    assert janice_ded == Money(Decimal("0"), AUD)


def test_allocate_threshold_insufficient_for_both():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("15000"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("40000"), AUD),
    )
    shared_deductions = [Money(Decimal("2000"), AUD)]

    from src.core.household import allocate_deductions

    your_ded, janice_ded = allocate_deductions(
        yours.income, janice.income, shared_deductions, fy=25
    )

    assert your_ded == Money(Decimal("2000"), AUD)
    assert janice_ded == Money(Decimal("0"), AUD)


def test_allocate_threshold_excess_to_lower_bracket():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("50000"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("30000"), AUD),
    )
    shared_deductions = [Money(Decimal("10000"), AUD)]

    from src.core.household import allocate_deductions

    your_ded, janice_ded = allocate_deductions(
        yours.income, janice.income, shared_deductions, fy=25
    )

    assert your_ded == Money(Decimal("0"), AUD)
    assert janice_ded == Money(Decimal("10000"), AUD)
