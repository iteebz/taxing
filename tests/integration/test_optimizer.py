from decimal import Decimal

from src.core.models import AUD, Money
from src.core.optimizer import (
    Individual,
    Year,
    current_bracket,
    greedy_allocation,
)


def test_optimizer_real_scenario_tyson_janice():
    """Real scenario: tyson ($150k) and janice ($50k) with shared deduction pool.

    Scenario:
    - tyson: $150k employment income, currently in 37% bracket
    - janice: $50k employment income, currently in 30% bracket
    - Shared deductions: $50k

    Greedy approach assigns all $50k to janice first (lower bracket).
    janice saves 30% = $15k on $50k deduction.

    Total savings: $15k
    """
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("150000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson, "janice": janice})

    shared_deductions = [Money(Decimal("50000"), AUD)]

    allocation = greedy_allocation(year, shared_deductions)

    janice_allocated = allocation["janice"].amount
    tyson_allocated = allocation["tyson"].amount

    janice_rate = current_bracket(janice)
    tyson_rate = current_bracket(tyson)

    janice_savings = janice_allocated * janice_rate
    tyson_savings = tyson_allocated * tyson_rate
    total_savings = janice_savings + tyson_savings

    assert janice_allocated == Decimal("50000")
    assert tyson_allocated == Decimal("0")
    assert janice_rate == Decimal("0.30")
    assert tyson_rate == Decimal("0.37")
    assert janice_savings == Decimal("15000")
    assert tyson_savings == Decimal("0")
    assert total_savings == Decimal("15000")


def test_optimizer_threshold_case():
    """Edge case: janice exactly at bracket threshold.

    At exactly $45k, janice is AT the 30% bracket threshold, so current_bracket
    returns 0.30. Headroom to next bracket ($135k) is $90k.
    """
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("45000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"janice": janice})

    deductions = [Money(Decimal("10000"), AUD)]

    allocation = greedy_allocation(year, deductions)

    assert allocation["janice"] == Money(Decimal("10000"), AUD)
    assert current_bracket(janice) == Decimal("0.30")
