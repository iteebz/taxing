from pathlib import Path

from src.core.property import aggregate_expenses
from src.io.property import load_property_expenses


def handle(args):
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


def register(subparsers):
    """Register property command."""
    parser = subparsers.add_parser("property", help="Aggregate property expenses")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--person", required=True, help="Person name")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
