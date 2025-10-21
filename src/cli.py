import argparse
import json
from decimal import Decimal
from pathlib import Path

from src.core.depreciation import depreciation_schedule
from src.core.models import AUD, Asset, Money
from src.core.optimizer import Individual, Year, greedy_allocation
from src.core.planning import plan_gains
from src.core.property import aggregate_expenses
from src.io.persist import dicts_from_csv
from src.io.property import load_property_expenses


def load_employment_income(base_dir: Path, fy: int) -> dict[str, Decimal]:
    """Load employment income per person from config file.

    Expected format: employment_income.json with mapping {person: amount}
    """
    config_file = base_dir / f"employment_income_fy{fy}.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"Missing employment income config: {config_file}\n"
            'Expected format: {"alice": 150000, "bob": 50000}'
        )

    with open(config_file) as f:
        data = json.load(f)

    return {k: Decimal(str(v)) for k, v in data.items()}


def get_tax_brackets(fy: int) -> list[tuple[Decimal, Decimal]]:
    """Get tax brackets for fiscal year."""
    if fy == 25:
        return [
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ]
    raise ValueError(f"Tax brackets not configured for FY{fy}")


def load_deductions(base_dir: Path, fy: int, person: str) -> list[Money]:
    """Load deductions for a person from Phase 1 output."""
    deductions_file = base_dir / "data" / f"fy{fy}" / person / "data" / "deductions.csv"
    if not deductions_file.exists():
        return []

    data = dicts_from_csv(deductions_file)
    total = Decimal("0")
    for row in data:
        if "amount" in row:
            total += Decimal(str(row["amount"]))

    return [Money(total, AUD)] if total > 0 else []


def cmd_optimize(args):
    """Optimize deduction allocation across persons to minimize tax liability."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    persons = args.persons.split(",") if args.persons else []

    if not persons:
        raise ValueError("--persons required (comma-separated list)")

    employment_income = load_employment_income(base_dir, fy)
    tax_brackets = get_tax_brackets(fy)

    missing = set(persons) - set(employment_income.keys())
    if missing:
        raise ValueError(f"Missing employment income for: {missing}")

    individuals = {}
    all_deductions = []

    for person in persons:
        emp_income = employment_income[person]
        deductions = load_deductions(base_dir, fy, person)
        all_deductions.extend(deductions)

        individuals[person] = Individual(
            name=person,
            employment_income=Money(emp_income, AUD),
            tax_brackets=tax_brackets,
            available_losses=Money(Decimal("0"), AUD),
        )

    year = Year(fy=fy, persons=individuals)
    allocation = greedy_allocation(year, all_deductions)

    print(f"\n{'Person':<15} {'Employment':<15} {'Deductions':<15} {'Bracket':<8} {'Savings':<12}")
    print("-" * 75)

    total_deductions = sum(d.amount for d in all_deductions)
    total_savings = Decimal("0")

    for person in sorted(persons):
        ind = individuals[person]
        alloc = allocation[person]
        bracket = ind.tax_brackets[-1][1]

        for threshold, rate in reversed(ind.tax_brackets):
            if ind.employment_income.amount >= threshold:
                bracket = rate
                break

        savings = alloc.amount * bracket
        total_savings += savings

        print(
            f"{person:<15} "
            f"${ind.employment_income.amount:<14,.0f} "
            f"${alloc.amount:<14,.0f} "
            f"{bracket * 100:<7.0f}% "
            f"${savings:<11,.0f}"
        )

    print("-" * 75)
    print(f"{'TOTAL':<15} {'':<15} ${total_deductions:<14,.0f} {'':<8} ${total_savings:<11,.0f}")


def cmd_property(args):
    """Aggregate property expenses (rent, water, council, strata)."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person

    expenses = load_property_expenses(base_dir, fy, person)
    if not expenses:
        print(f"\nNo property expenses found for {person} FY{fy}")
        return

    summary = aggregate_expenses(expenses)

    print(f"\nProperty Expenses - {person} FY{fy}")
    print("-" * 50)
    print(f"{'Rent':<20} ${summary.rent.amount:>15,.2f}")
    print(f"{'Water':<20} ${summary.water.amount:>15,.2f}")
    print(f"{'Council Rates':<20} ${summary.council.amount:>15,.2f}")
    print(f"{'Strata/Body Corp':<20} ${summary.strata.amount:>15,.2f}")
    print("-" * 50)
    print(f"{'TOTAL':<20} ${summary.total.amount:>15,.2f}")


def cmd_gains_plan(args):
    """Plan multi-year capital gains realization with loss carryforward."""
    bracket_parts = args.projection.split(",")
    bracket_projection = {}

    for part in bracket_parts:
        fy_str, rate_str = part.split(":")
        fy = int(fy_str)
        rate = int(rate_str.rstrip("%"))
        bracket_projection[fy] = rate

    gains = args.gains if hasattr(args, "gains") else []
    losses = args.losses if hasattr(args, "losses") else []

    if not gains:
        print("\nNo gains provided for planning")
        return

    plan = plan_gains(gains, losses, bracket_projection)

    print("\nMulti-Year Gains Plan")
    print("-" * 80)
    print(f"{'Year':<8} {'Realized':<15} {'Bracket':<10} {'CF Used':<15} {'Taxable':<15}")
    print("-" * 80)

    for fy in sorted(plan.keys()):
        p = plan[fy]
        bracket_rate = bracket_projection.get(fy, 0)
        print(
            f"FY{fy:<6} "
            f"${sum(g.taxable_gain.amount for g in p.realized_gains):<14,.0f} "
            f"{bracket_rate:<9}% "
            f"${p.carryforward_used.amount:<14,.0f} "
            f"${p.taxable_gain.amount:<14,.0f}"
        )

    print("-" * 80)


def cmd_asset_depreciation(args):
    """Calculate prime cost depreciation for asset."""
    asset = Asset(
        fy=args.fy_purchased,
        description=args.description,
        cost=Money(Decimal(str(args.cost)), AUD),
        life_years=args.life_years,
    )

    to_fy = args.to_fy or args.fy_purchased + 5
    schedule = depreciation_schedule(asset, to_fy)

    print(f"\nAsset Depreciation Schedule - {asset.description}")
    print(f"Cost: ${asset.cost.amount:,.2f} | Life: {asset.life_years} years | Method: Prime Cost")
    print("-" * 60)
    print(f"{'Year':<10} {'Annual Deduction':<20} {'Cumulative':<20}")
    print("-" * 60)

    cumulative = Decimal("0")
    for fy in sorted(schedule.keys()):
        annual = schedule[fy].amount
        cumulative += annual
        print(f"FY{fy:<8} ${annual:<19,.2f} ${cumulative:<19,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Tax optimization and management tool",
        prog="tax",
    )
    subparsers = parser.add_subparsers(dest="command")

    opt_parser = subparsers.add_parser("optimize", help="Optimize deduction allocation")
    opt_parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    opt_parser.add_argument("--persons", required=True, help="Comma-separated person names")
    opt_parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    opt_parser.set_defaults(func=cmd_optimize)

    prop_parser = subparsers.add_parser("property", help="Aggregate property expenses")
    prop_parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    prop_parser.add_argument("--person", required=True, help="Person name")
    prop_parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    prop_parser.set_defaults(func=cmd_property)

    plan_parser = subparsers.add_parser("gains-plan", help="Plan multi-year gains realization")
    plan_parser.add_argument(
        "--projection",
        required=True,
        help="Tax projection: 25:30%,26:45%,27:30%",
    )
    plan_parser.add_argument("--gains", type=json.loads, default="[]", help="Gains JSON array")
    plan_parser.add_argument("--losses", type=json.loads, default="[]", help="Losses JSON array")
    plan_parser.set_defaults(func=cmd_gains_plan)

    asset_parser = subparsers.add_parser("asset-depreciation", help="Calculate asset depreciation")
    asset_parser.add_argument("--description", required=True, help="Asset description")
    asset_parser.add_argument("--cost", type=float, required=True, help="Asset cost in AUD")
    asset_parser.add_argument(
        "--fy-purchased", type=int, required=True, help="FY purchased (e.g., 25)"
    )
    asset_parser.add_argument("--life-years", type=int, required=True, help="Useful life in years")
    asset_parser.add_argument(
        "--to-fy", type=int, help="Generate schedule to FY (default: fy_purchased + 5)"
    )
    asset_parser.set_defaults(func=cmd_asset_depreciation)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
