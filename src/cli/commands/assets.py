from decimal import Decimal

from src.core.depreciation import depreciation_schedule
from src.core.models import AUD, Asset, Money


def handle(args):
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


def register(subparsers):
    """Register asset-depreciation command."""
    parser = subparsers.add_parser("asset-depreciation", help="Calculate asset depreciation")
    parser.add_argument("--description", required=True, help="Asset description")
    parser.add_argument("--cost", type=float, required=True, help="Asset cost in AUD")
    parser.add_argument(
        "--fy-purchased", type=int, required=True, help="FY purchased (e.g., 25)"
    )
    parser.add_argument("--life-years", type=int, required=True, help="Useful life in years")
    parser.add_argument(
        "--to-fy", type=int, help="Generate schedule to FY (default: fy_purchased + 5)"
    )
    parser.set_defaults(func=handle)
