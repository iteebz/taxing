from dataclasses import replace
from datetime import date
from decimal import Decimal

from src.core.models import Gain, Position, Trade


def calc_fy(d: date) -> int:
    """Calculate financial year (FY starts July 1)."""
    return d.year if d.month < 7 else d.year + 1


def is_cgt_discount_eligible(hold_days: int) -> bool:
    """CGT discount eligibility: held ≥365 days (12 months)."""
    return hold_days >= 365


def _fee_per_unit(total_fee: Decimal, units: Decimal) -> Decimal:
    """Calculate fee allocated per unit."""
    if not units or units <= 0:
        return Decimal("0")
    return total_fee / units


def get_positions(trades: list[Trade]) -> dict[str, Position]:
    """Derive current positions from trade history."""
    positions: dict[str, tuple[Decimal, Decimal]] = {}

    for trade in sorted(trades, key=lambda t: (t.code, t.date)):
        if trade.code not in positions:
            positions[trade.code] = (Decimal("0"), Decimal("0"))

        units, cost_basis = positions[trade.code]

        if trade.action == "buy":
            units += trade.units
            cost_basis += trade.units * trade.price + trade.fee
        else:
            if units > 0:
                cost_basis *= (units - trade.units) / units
                units -= trade.units

        positions[trade.code] = (units, cost_basis)

    return {
        code: Position(ticker=code, units=units, total_cost_basis=cost_basis)
        for code, (units, cost_basis) in positions.items()
        if units > 0
    }


def _lot_sort_priority(lot: Trade, sell_price: Decimal, sell_date: date) -> tuple:
    """Sort key for lot selection: prioritize losses, then discounted positions, then FIFO."""
    is_loss = lot.price >= sell_price
    hold_days = (sell_date - lot.date).days
    is_discounted = is_cgt_discount_eligible(hold_days)
    return (not is_loss, not is_discounted, lot.date)


def process_trades(trades: list[Trade]) -> list[Gain]:
    """Process trades using FIFO with loss harvesting + CGT discount prioritization."""

    results = []
    buffers: dict[str, list[Trade]] = {}
    sorted_trades = sorted(trades, key=lambda t: (t.code, t.date))

    for trade in sorted_trades:
        if trade.action == "buy":
            if trade.code not in buffers:
                buffers[trade.code] = []
            buffers[trade.code].append(trade)
        else:
            buff = buffers.get(trade.code, [])
            units_to_sell = trade.units
            fy = calc_fy(trade.date)

            sell_fee_per_unit = _fee_per_unit(trade.fee, trade.units)

            while buff and units_to_sell > Decimal(0):
                sell_lot = min(buff, key=lambda t: _lot_sort_priority(t, trade.price, trade.date))
                hold_days = (trade.date - sell_lot.date).days
                is_discounted = is_cgt_discount_eligible(hold_days)

                trade.units * (trade.price - sell_lot.price)

                if units_to_sell >= sell_lot.units:
                    units_matched = sell_lot.units
                    profit = units_matched * (trade.price - sell_lot.price)
                    profit -= sell_lot.fee
                    profit -= units_matched * sell_fee_per_unit
                    gain = profit / 2 if is_discounted else profit

                    results.append(
                        Gain(
                            fy=fy,
                            raw_profit=profit,
                            taxable_gain=gain,
                        )
                    )

                    buff.remove(sell_lot)
                    units_to_sell -= units_matched
                else:
                    units_matched = units_to_sell
                    profit = units_matched * (trade.price - sell_lot.price)
                    partial_fee = (units_matched / sell_lot.units) * sell_lot.fee
                    profit -= partial_fee
                    profit -= units_matched * sell_fee_per_unit
                    gain = profit / 2 if is_discounted else profit

                    results.append(
                        Gain(
                            fy=fy,
                            raw_profit=profit,
                            taxable_gain=gain,
                        )
                    )

                    updated_lot = replace(
                        sell_lot,
                        units=sell_lot.units - units_to_sell,
                        fee=sell_lot.fee - partial_fee,
                    )
                    buff[buff.index(sell_lot)] = updated_lot
                    units_to_sell = Decimal(0)

    return results
