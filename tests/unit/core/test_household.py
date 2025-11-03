from decimal import Decimal

from src.core.household import (
    _tax_liability,
    allocate_deductions,
    calculate_tax,
    optimize_household,
)
from src.core.models import Gain, Individual, Loss


def test_calculate_tax_single():
    ind = Individual(
        name="alice",
        fy=25,
        income=Decimal("60000"),
        deductions=[Decimal("5000")],
    )
    result = calculate_tax(ind)
    assert result.individual == ind
    assert result.liability.income_tax > Decimal("0")
    assert result.liability.total > Decimal("0")


def test_taxable_with_deduc():
    ind = Individual(
        name="you",
        fy=25,
        income=Decimal("50000"),
        deductions=[Decimal("5000"), Decimal("2000")],
    )
    assert ind.taxable_income == Decimal("43000")


def test_taxable_gains_loss():
    gains = [
        Gain(
            individual="you",
            fy=25,
            raw_profit=Decimal("1000"),
            taxable_gain=Decimal("500"),
        ),
        Gain(
            individual="you",
            fy=25,
            raw_profit=Decimal("-100"),
            taxable_gain=Decimal("-100"),
        ),
    ]
    ind = Individual(
        name="you",
        fy=25,
        income=Decimal("50000"),
        gains=gains,
    )
    assert ind.taxable_income == Decimal("50400")


def test_tax_under_thresh():
    liability = _tax_liability(Decimal("10000"), 25)
    assert liability.income_tax == Decimal("0")
    assert liability.medicare_levy == Decimal("0")
    assert liability.total == Decimal("0")


def test_tax_basic():
    liability = _tax_liability(Decimal("50000"), 25)
    b1 = (Decimal("45000") - Decimal("18200")) * Decimal("0.16")
    b2 = (Decimal("50000") - Decimal("45000")) * Decimal("0.30")
    expected_income_tax = b1 + b2
    assert liability.income_tax == expected_income_tax
    assert liability.medicare_levy == Decimal("1000")
    assert liability.total == expected_income_tax + Decimal("1000")


def test_low_inc_medicare():
    liability = _tax_liability(Decimal("26000"), 25)
    full_levy = Decimal("26000") * Decimal("0.02")
    reduced_levy = (Decimal("26000") - Decimal("24276")) * Decimal("0.10")
    assert liability.medicare_levy == min(full_levy, reduced_levy)


def test_high_inc_medicare():
    liability = _tax_liability(Decimal("120000"), 25)
    assert liability.medicare_levy == Decimal("2400")
    assert liability.total == liability.income_tax + Decimal("2400")


def test_opt_deduc_lower_bracket():
    yours = Individual(
        name="you",
        fy=25,
        income=Decimal("80000"),
        deductions=[Decimal("5000")],
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Decimal("40000"),
        deductions=[Decimal("2000")],
    )

    result = optimize_household(yours, janice)

    assert result.yours.total_deductions == Decimal("7000")
    assert result.janice.total_deductions == Decimal("0")


def test_opt_preserve_gains_loss():
    gains = [
        Gain(
            individual="you",
            fy=25,
            raw_profit=Decimal("1000"),
            taxable_gain=Decimal("500"),
        )
    ]
    [Loss(fy=25, amount=Decimal("100"), source_fy=24)]

    yours = Individual(
        name="you",
        fy=25,
        income=Decimal("50000"),
        gains=gains,
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Decimal("40000"),
    )

    result = optimize_household(yours, janice)

    assert result.yours.gains == gains


def test_opt_household_tax():
    yours = Individual(
        name="you",
        fy=25,
        income=Decimal("80000"),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Decimal("40000"),
    )

    result = optimize_household(yours, janice)

    assert result.total == result.your_liability.total + result.janice_liability.total


def test_opt_family_medicare():
    yours = Individual(
        name="you",
        fy=24,
        income=Decimal("24500"),
    )
    janice = Individual(
        name="janice",
        fy=24,
        income=Decimal("16000"),
    )

    result = optimize_household(yours, janice)

    assert result.your_liability.medicare_levy == Decimal("0")
    assert result.janice_liability.medicare_levy == Decimal("0")


def test_alloc_you_empty_janice_full():
    tyson_deduction, janice_deduction = allocate_deductions(
        Decimal("0"),
        Decimal("30000"),
        [Decimal("5000"), Decimal("3000")],
        fy=25,
    )

    assert tyson_deduction == Decimal("0")
    assert janice_deduction == Decimal("8000")


def test_alloc_you_buffer_janice_over():
    tyson_deduction, janice_deduction = allocate_deductions(
        Decimal("10000"),
        Decimal("60000"),
        [Decimal("5000"), Decimal("5000")],
        fy=25,
    )

    assert tyson_deduction == Decimal("0")
    assert janice_deduction == Decimal("10000")


def test_alloc_both_under():
    tyson_deduction, janice_deduction = allocate_deductions(
        Decimal("15000"),
        Decimal("16000"),
        [Decimal("3000")],
        fy=25,
    )

    assert tyson_deduction == Decimal("0")
    assert janice_deduction == Decimal("3000")


def test_alloc_insufficient():
    tyson_deduction, janice_deduction = allocate_deductions(
        Decimal("10000"),
        Decimal("20000"),
        [Decimal("2000")],
        fy=25,
    )

    assert tyson_deduction == Decimal("0")
    assert janice_deduction == Decimal("2000")


def test_alloc_excess_lower():
    tyson_deduction, janice_deduction = allocate_deductions(
        Decimal("50000"),
        Decimal("30000"),
        [Decimal("10000")],
        fy=25,
    )

    assert tyson_deduction == Decimal("10000")
    assert janice_deduction == Decimal("0")
