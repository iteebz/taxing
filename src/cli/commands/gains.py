import typer

from src.core.planning import plan_gains


def handle(
    projection: str = typer.Option(..., "--projection", help="Tax projection: 25:30%,26:45%"),
    gains: list[float] = typer.Option(None, "--gains", help="Gains list (repeatable)"),
    losses: list[float] = typer.Option(None, "--losses", help="Losses list (repeatable)"),
):
    """Plan multi-year gains realization with loss carryforward."""
    bracket_parts = projection.split(",")
    bracket_projection = {}

    for part in bracket_parts:
        fy_str, rate_str = part.split(":")
        fy = int(fy_str)
        rate = int(rate_str.rstrip("%"))
        bracket_projection[fy] = rate

    gains_list = gains if gains else []
    losses_list = losses if losses else []

    if not gains_list:
        print("\nNo gains provided for planning")
        return

    plan = plan_gains(gains_list, losses_list, bracket_projection)

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
