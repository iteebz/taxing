"""Phase 2c multi-year gains planning CLI integration tests."""

from decimal import Decimal

from src.cli import cmd_gains_plan
from src.core.models import AUD, Gain, Loss, Money


class Args:
    """Mock argparse Namespace for testing."""

    def __init__(self, projection, gains=None, losses=None):
        self.projection = projection
        self.gains = gains or []
        self.losses = losses or []


def test_gains_plan_single_year(capsys):
    """Plan gains in single year with no carryforwards."""
    gains = [
        Gain(
            fy=25,
            raw_profit=Money(Decimal("10000"), AUD),
            taxable_gain=Money(Decimal("5000"), AUD),
            action="discount",
        ),
    ]
    losses = []

    args = Args(projection="25:30%", gains=gains, losses=losses)
    cmd_gains_plan(args)

    captured = capsys.readouterr()
    assert "FY25" in captured.out
    assert "5000" in captured.out or "5,000" in captured.out
    assert "30" in captured.out


def test_gains_plan_multi_year(capsys):
    """Plan gains across multiple years."""
    gains = [
        Gain(
            fy=25,
            raw_profit=Money(Decimal("10000"), AUD),
            taxable_gain=Money(Decimal("5000"), AUD),
            action="discount",
        ),
        Gain(
            fy=26,
            raw_profit=Money(Decimal("10000"), AUD),
            taxable_gain=Money(Decimal("5000"), AUD),
            action="discount",
        ),
    ]
    losses = []

    args = Args(projection="25:30%,26:45%", gains=gains, losses=losses)
    cmd_gains_plan(args)

    captured = capsys.readouterr()
    assert "FY25" in captured.out
    assert "FY26" in captured.out
    assert "30" in captured.out
    assert "45" in captured.out


def test_gains_plan_with_loss_carryforward(capsys):
    """Plan gains with loss carryforward offset."""
    gains = [
        Gain(
            fy=26,
            raw_profit=Money(Decimal("8000"), AUD),
            taxable_gain=Money(Decimal("8000"), AUD),
            action="discount",
        ),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("3000"), AUD), source_fy=25),
    ]

    args = Args(projection="26:30%", gains=gains, losses=losses)
    cmd_gains_plan(args)

    captured = capsys.readouterr()
    assert "FY26" in captured.out
    assert "3000" in captured.out or "3,000" in captured.out
    assert "5000" in captured.out or "5,000" in captured.out


def test_gains_plan_no_gains(capsys):
    """No gains provided returns graceful message."""
    args = Args(projection="25:30%", gains=[], losses=[])
    cmd_gains_plan(args)

    captured = capsys.readouterr()
    assert "No gains provided" in captured.out


def test_gains_plan_realistic_scenario(capsys):
    """Realistic multi-year scenario: low bracket FY25, high FY26, low FY27."""
    gains = [
        Gain(
            fy=25,
            raw_profit=Money(Decimal("8000"), AUD),
            taxable_gain=Money(Decimal("4000"), AUD),
            action="discount",
        ),
        Gain(
            fy=26,
            raw_profit=Money(Decimal("10000"), AUD),
            taxable_gain=Money(Decimal("5000"), AUD),
            action="discount",
        ),
        Gain(
            fy=27,
            raw_profit=Money(Decimal("12000"), AUD),
            taxable_gain=Money(Decimal("6000"), AUD),
            action="discount",
        ),
    ]
    losses = [
        Loss(fy=26, amount=Money(Decimal("2000"), AUD), source_fy=25),
    ]

    args = Args(projection="25:30%,26:45%,27:30%", gains=gains, losses=losses)
    cmd_gains_plan(args)

    captured = capsys.readouterr()
    assert "FY25" in captured.out
    assert "FY26" in captured.out
    assert "FY27" in captured.out
    assert "Multi-Year Gains Plan" in captured.out
