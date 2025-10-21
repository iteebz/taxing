from src.core.planning import plan_gains


def handle(args):
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
            f"${sum(g.taxable_gain for g in p.realized_gains):<14,.0f} "
            f"{bracket_rate:<9}% "
            f"${p.carryforward_used:<14,.0f} "
            f"${p.taxable_gain:<14,.0f}"
        )

    print("-" * 80)


def register(subparsers):
    """Register gains-plan command."""
    import json

    parser = subparsers.add_parser("gains-plan", help="Plan multi-year gains realization")
    parser.add_argument(
        "--projection",
        required=True,
        help="Tax projection: 25:30%,26:45%,27:30%",
    )
    parser.add_argument("--gains", type=json.loads, default="[]", help="Gains JSON array")
    parser.add_argument("--losses", type=json.loads, default="[]", help="Losses JSON array")
    parser.set_defaults(func=handle)
