from dataclasses import replace
from decimal import Decimal

from src.core.models import AUD, Gain, Money, Trade


def calc_fy(date) -> int:
    """Calculate financial year (FY starts July 1)."""
    return date.year if date.month < 7 else date.year + 1


def is_cgt_discount_eligible(hold_days: int) -> bool:
    """CGT discount eligibility: held >365 days."""
    return hold_days > 365


def process_trades(trades: list[Trade]) -> list[Gain]:
    """
    Process trades using FIFO with loss harvesting + CGT discount prioritization.

    Strategy:
    1. For each sell, prioritize loss positions (buy >= sell price)
    2. Then prioritize 365+ day holdings for CGT discount
    3. Fall back to FIFO (first in, first out)
    """
    results = []
    buff = []

    sorted_trades = sorted(trades, key=lambda t: (t.code, t.date))

    for trade in sorted_trades:
        if trade.action == "buy":
            buff.append(trade)
        else:
            units_to_sell = trade.units
            fy = calc_fy(trade.date)

            while len(buff) > 0 and units_to_sell > Decimal(0):
                loss_positions = [t for t in buff if t.price.amount >= trade.price.amount]
                disc_positions = [t for t in buff if (trade.date - t.date).days > 365]

                if loss_positions:
                    action = "loss"
                    sell_lot = loss_positions[0]
                elif disc_positions:
                    action = "discount"
                    sell_lot = disc_positions[0]
                else:
                    action = "fifo"
                    sell_lot = buff[0]

                hold_days = (trade.date - sell_lot.date).days
                is_discounted = is_cgt_discount_eligible(hold_days)

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
                    idx = buff.index(sell_lot)
                    buff[idx] = updated_lot
                    units_to_sell = Decimal(0)

    return results
