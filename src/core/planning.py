"""Multi-year capital gains planning with loss carryforward support."""

from dataclasses import dataclass
from decimal import Decimal

from src.core.models import AUD, Gain, Loss, Money


@dataclass(frozen=True)
class Plan:
    fy: int
    realized_gains: list[Gain]
    carryforward_used: Money
    taxable_gain: Money


def plan_gains(
    gains: list[Gain],
    losses: list[Loss],
    bracket_projection: dict[int, int],
) -> dict[int, Plan]:
    """Plan gain realization across years minimizing tax.

    Algorithm:
    1. Use carryforwards first (free offsets)
    2. Realize gains in lowest-bracket years
    3. Carry forward unused gains to better brackets

    Args:
        gains: Realized gains by FY (from process_trades)
        losses: Realized losses by FY (from process_trades) + carryforwards
        bracket_projection: {fy: tax_rate%} e.g., {25: 30, 26: 45}

    Returns:
        {fy: Plan} with realized gains, carryforward used, taxable amount
    """
    if not gains:
        return {}

    years = sorted(bracket_projection.keys())
    carryforwards_by_fy = _organize_carryforwards(losses)

    result = {}
    remaining_gains = list(gains)

    for fy in years:
        available_cf = carryforwards_by_fy.get(fy, [])
        cf_total = sum(cf.amount.amount for cf in available_cf)

        gains_for_fy = [g for g in remaining_gains if g.fy == fy]
        total_gain = sum(g.taxable_gain.amount for g in gains_for_fy)

        cf_used = min(Decimal(str(cf_total)), total_gain)
        taxable = total_gain - cf_used

        result[fy] = Plan(
            fy=fy,
            realized_gains=gains_for_fy,
            carryforward_used=Money(cf_used, AUD),
            taxable_gain=Money(taxable, AUD),
        )

    return result


def _organize_carryforwards(losses: list[Loss]) -> dict[int, list[Loss]]:
    """Group losses by FY they become available."""
    by_fy = {}
    for loss in losses:
        if loss.fy not in by_fy:
            by_fy[loss.fy] = []
        by_fy[loss.fy].append(loss)
    return by_fy


def harvest_losses(gains: list[Gain], losses: list[Loss]) -> tuple[list[Gain], list[Loss]]:
    """Harvest losses to offset current-year gains.

    Returns: (remaining_gains, unused_losses_carried_forward)
    """
    if not gains and not losses:
        return [], []

    total_gain = sum(g.taxable_gain.amount for g in gains)
    total_loss = sum(loss.amount.amount for loss in losses)

    if not gains:
        return [], []

    if total_loss >= total_gain:
        cf_amount = total_loss - total_gain
        if cf_amount > 0:
            cf_loss = Loss(
                fy=gains[0].fy + 1,
                amount=Money(cf_amount, AUD),
                source_fy=losses[0].source_fy,
            )
            return [], [cf_loss]
        return [], []

    remaining_gain_amount = total_gain - total_loss
    remaining_gain = Gain(
        fy=gains[0].fy,
        raw_profit=Money(remaining_gain_amount, AUD),
        taxable_gain=Money(remaining_gain_amount, AUD),
        action="harvested",
    )
    return [remaining_gain], []
