"""Multi-year gains planning tests."""

from decimal import Decimal

from src.core.models import AUD, Gain, Loss, Money
from src.core.planning import harvest_losses, plan_gains


def test_plan_single_year_no_losses():
    """Plan gains in single year with no carryforwards."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = []
    bracket = {25: 30}

    plan = plan_gains(gains, losses, bracket)

    assert 25 in plan
    assert plan[25].taxable_gain == Money(Decimal("5000"), AUD)
    assert plan[25].carryforward_used == Money(Decimal("0"), AUD)


def test_plan_multi_year_lowest_bracket_first():
    """Gains realized in lowest-bracket years first."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
        Gain(fy=26, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = []
    bracket = {25: 30, 26: 45}

    plan = plan_gains(gains, losses, bracket)

    assert 25 in plan
    assert 26 in plan
    assert plan[25].taxable_gain == Money(Decimal("5000"), AUD)
    assert plan[26].taxable_gain == Money(Decimal("5000"), AUD)


def test_plan_with_carryforward_full_offset():
    """Carryforward fully offsets current-year gain."""
    gains = [
        Gain(fy=26, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("5000"), AUD), source_fy=25),
    ]
    bracket = {26: 30}

    plan = plan_gains(gains, losses, bracket)

    assert plan[26].carryforward_used == Money(Decimal("5000"), AUD)
    assert plan[26].taxable_gain == Money(Decimal("0"), AUD)


def test_plan_with_carryforward_partial_offset():
    """Carryforward partially offsets current-year gain."""
    gains = [
        Gain(fy=26, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("8000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("3000"), AUD), source_fy=25),
    ]
    bracket = {26: 30}

    plan = plan_gains(gains, losses, bracket)

    assert plan[26].carryforward_used == Money(Decimal("3000"), AUD)
    assert plan[26].taxable_gain == Money(Decimal("5000"), AUD)


def test_plan_with_carryforward_excess():
    """Carryforward exceeds current-year gain, rest carried forward."""
    gains = [
        Gain(fy=26, raw_profit=Money(Decimal("5000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("10000"), AUD), source_fy=25),
    ]
    bracket = {26: 30}

    plan = plan_gains(gains, losses, bracket)

    assert plan[26].carryforward_used == Money(Decimal("5000"), AUD)
    assert plan[26].taxable_gain == Money(Decimal("0"), AUD)


def test_plan_multiple_carryforwards_stacked():
    """Multiple carryforwards applied sequentially."""
    gains = [
        Gain(fy=27, raw_profit=Money(Decimal("15000"), AUD), taxable_gain=Money(Decimal("15000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=27, amount=Money(Decimal("5000"), AUD), source_fy=25),
        Loss(fy=27, amount=Money(Decimal("3000"), AUD), source_fy=26),
    ]
    bracket = {27: 30}

    plan = plan_gains(gains, losses, bracket)

    assert plan[27].carryforward_used == Money(Decimal("8000"), AUD)
    assert plan[27].taxable_gain == Money(Decimal("7000"), AUD)


def test_plan_no_gains():
    """No gains returns empty plan."""
    plan = plan_gains([], [], {25: 30, 26: 45})
    assert plan == {}


def test_harvest_losses_full_offset():
    """Loss harvest fully offsets gain."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("5000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=25, amount=Money(Decimal("5000"), AUD), source_fy=24),
    ]

    remaining_gains, carryforwards = harvest_losses(gains, losses)

    assert len(remaining_gains) == 0
    assert len(carryforwards) == 0


def test_harvest_losses_partial_offset():
    """Loss harvest partially offsets gain."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("8000"), AUD), taxable_gain=Money(Decimal("8000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=25, amount=Money(Decimal("3000"), AUD), source_fy=24),
    ]

    remaining_gains, carryforwards = harvest_losses(gains, losses)

    assert len(remaining_gains) == 1
    assert remaining_gains[0].taxable_gain == Money(Decimal("5000"), AUD)
    assert len(carryforwards) == 0


def test_harvest_losses_excess_carryforward():
    """Excess loss carried forward to next year."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("3000"), AUD), taxable_gain=Money(Decimal("3000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=25, amount=Money(Decimal("8000"), AUD), source_fy=24),
    ]

    remaining_gains, carryforwards = harvest_losses(gains, losses)

    assert len(remaining_gains) == 0
    assert len(carryforwards) == 1
    assert carryforwards[0].amount == Money(Decimal("5000"), AUD)
    assert carryforwards[0].fy == 26


def test_harvest_losses_no_losses():
    """No losses to harvest returns gains unchanged."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("5000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
    ]
    losses = []

    remaining_gains, carryforwards = harvest_losses(gains, losses)

    assert len(remaining_gains) == 1
    assert remaining_gains[0].taxable_gain == Money(Decimal("5000"), AUD)
    assert len(carryforwards) == 0


def test_harvest_losses_no_gains():
    """No gains but losses to carry forward."""
    gains = []
    losses = [
        Loss(fy=25, amount=Money(Decimal("5000"), AUD), source_fy=24),
    ]

    remaining_gains, carryforwards = harvest_losses(gains, losses)

    assert len(remaining_gains) == 0
    assert len(carryforwards) == 0


def test_plan_realistic_scenario():
    """Realistic multi-year scenario: defer gain, harvest loss, then realize."""
    gains = [
        Gain(fy=25, raw_profit=Money(Decimal("8000"), AUD), taxable_gain=Money(Decimal("4000"), AUD), action="discount"),
        Gain(fy=26, raw_profit=Money(Decimal("10000"), AUD), taxable_gain=Money(Decimal("5000"), AUD), action="discount"),
        Gain(fy=27, raw_profit=Money(Decimal("12000"), AUD), taxable_gain=Money(Decimal("6000"), AUD), action="discount"),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("2000"), AUD), source_fy=25),
    ]
    bracket = {25: 45, 26: 30, 27: 30}

    plan = plan_gains(gains, losses, bracket)

    assert plan[25].taxable_gain == Money(Decimal("4000"), AUD)
    assert plan[26].taxable_gain == Money(Decimal("3000"), AUD)
    assert plan[26].carryforward_used == Money(Decimal("2000"), AUD)
    assert plan[27].taxable_gain == Money(Decimal("6000"), AUD)
