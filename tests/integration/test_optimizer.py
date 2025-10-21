from decimal import Decimal

from src.core.models import AUD, Money
from src.core.optimizer import (
    Individual,
    Year,
    current_bracket,
    greedy_allocation,
)


def test_optimizer_real_scenario_alice_bob():
    """Real scenario: Alice ($150k) and Bob ($50k) with shared deduction pool.
    
    Scenario:
    - Alice: $150k employment income, currently in 37% bracket
    - Bob: $50k employment income, currently in 30% bracket
    - Shared deductions: $50k
    
    Greedy approach assigns all $50k to Bob first (lower bracket).
    Bob saves 30% = $15k on $50k deduction.
    
    Total savings: $15k
    """
    alice = Individual(
        name="alice",
        employment_income=Money(Decimal("150000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    bob = Individual(
        name="bob",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    
    year = Year(fy=25, persons={"alice": alice, "bob": bob})
    
    shared_deductions = [Money(Decimal("50000"), AUD)]
    
    allocation = greedy_allocation(year, shared_deductions)
    
    bob_allocated = allocation["bob"].amount
    alice_allocated = allocation["alice"].amount
    
    bob_rate = current_bracket(bob)
    alice_rate = current_bracket(alice)
    
    bob_savings = bob_allocated * bob_rate
    alice_savings = alice_allocated * alice_rate
    total_savings = bob_savings + alice_savings
    
    assert bob_allocated == Decimal("50000")
    assert alice_allocated == Decimal("0")
    assert bob_rate == Decimal("0.30")
    assert alice_rate == Decimal("0.37")
    assert bob_savings == Decimal("15000")
    assert alice_savings == Decimal("0")
    assert total_savings == Decimal("15000")


def test_optimizer_threshold_case():
    """Edge case: Bob exactly at bracket threshold.
    
    At exactly $45k, Bob is AT the 30% bracket threshold, so current_bracket
    returns 0.30. Headroom to next bracket ($135k) is $90k.
    """
    bob = Individual(
        name="bob",
        employment_income=Money(Decimal("45000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    
    year = Year(fy=25, persons={"bob": bob})
    
    deductions = [Money(Decimal("10000"), AUD)]
    
    allocation = greedy_allocation(year, deductions)
    
    assert allocation["bob"] == Money(Decimal("10000"), AUD)
    assert current_bracket(bob) == Decimal("0.30")


def test_optimizer_three_persons_cascade():
    """Three persons: deductions cascade down bracket levels."""
    alice = Individual(
        name="alice",
        employment_income=Money(Decimal("200000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    bob = Individual(
        name="bob",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    charlie = Individual(
        name="charlie",
        employment_income=Money(Decimal("30000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    
    year = Year(fy=25, persons={"alice": alice, "bob": bob, "charlie": charlie})
    
    deductions = [Money(Decimal("40000"), AUD)]
    
    allocation = greedy_allocation(year, deductions)
    
    assert allocation["charlie"] == Money(Decimal("15000"), AUD)
    assert allocation["bob"] == Money(Decimal("25000"), AUD)
    assert allocation["alice"] == Money(Decimal("0"), AUD)
