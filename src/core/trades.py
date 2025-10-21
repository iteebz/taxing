from dataclasses import replace
from datetime import date
from decimal import Decimal

from src.core.models import AUD, Gain, Money, Trade


def calc_fy(d: date) -> int:
    """Calculate financial year (FY starts July 1)."""
    return d.year if d.month < 7 else d.year + 1


def is_cgt_discount_eligible(hold_days: int) -> bool:
    """CGT discount eligibility: held >365 days."""
    return hold_days > 365


def process_trades(trades: list[Trade]) -> list[Gain]:
    """
    Process trades using FIFO with loss harvesting + CGT discount prioritization.

    Priority: losses > discounted (365+ days) > FIFO (oldest first).
    Per-ticker buffers prevent cross-contamination.
    """

    def sort_priority(lot: Trade, sell_price: Decimal, sell_date: date) -> tuple:
        is_loss = lot.price.amount >= sell_price
        is_discounted = (sell_date - lot.date).days > 365
        return (not is_loss, not is_discounted, lot.date)

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

            while buff and units_to_sell > Decimal(0):
                sell_lot = min(buff, key=lambda t: sort_priority(t, trade.price.amount, trade.date))
                hold_days = (trade.date - sell_lot.date).days
                is_discounted = is_cgt_discount_eligible(hold_days)

                is_loss = sell_lot.price.amount >= trade.price.amount
                action = "loss" if is_loss else ("discount" if is_discounted else "fifo")

                if units_to_sell >= sell_lot.units:
                    profit = sell_lot.units * (trade.price.amount - sell_lot.price.amount)
                    profit -= sell_lot.fee.amount
                    gain = profit / 2 if is_discounted else profit

                    results.append(
                        Gain(
                            fy=fy,
                            raw_profit=Money(profit, AUD),
                            taxable_gain=Money(gain, AUD),
                            action=action,
                        )
                    )

                    buff.remove(sell_lot)
                    units_to_sell -= sell_lot.units
                else:
                    profit = units_to_sell * (trade.price.amount - sell_lot.price.amount)
                    partial_fee = (units_to_sell / sell_lot.units) * sell_lot.fee.amount
                    profit -= partial_fee
                    gain = profit / 2 if is_discounted else profit

                    results.append(
                        Gain(
                            fy=fy,
                            raw_profit=Money(profit, AUD),
                            taxable_gain=Money(gain, AUD),
                            action=action,
                        )
                    )

                    updated_lot = replace(
                        sell_lot,
                        units=sell_lot.units - units_to_sell,
                        fee=Money(sell_lot.fee.amount - partial_fee, AUD),
                    )
                    buff[buff.index(sell_lot)] = updated_lot
                    units_to_sell = Decimal(0)

    return results
