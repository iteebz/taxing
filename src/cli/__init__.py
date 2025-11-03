import typer

from src.cli.commands import coverage, gains, metrics, mining, optimize, property, run

app = typer.Typer(
    name="tax",
    help="Tax optimization and management tool",
    no_args_is_help=False,
)


@app.command(name="run")
def cmd_run(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Run full tax pipeline (ingest → classify → deduce → trades → persist)."""
    run.handle(fy, base_dir)


@app.command(name="coverage")
def cmd_coverage(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    sample: int = typer.Option(None, "--sample", help="Sample N uncategorized transactions"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Show coverage gaps & sample uncategorized transactions."""
    coverage.handle(fy, person, sample, base_dir)


@app.command(name="mine")
def cmd_mine(
    fy: int = typer.Option(None, "--fy", help="Fiscal year (e.g., 25), omit to process all"),
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    search: bool = typer.Option(False, "--search", help="Enable search for categorization hints"),
    show_unlabeled: bool = typer.Option(
        False, "--show-unlabeled", help="Show unlabeled txns + search results"
    ),
    threshold: int = typer.Option(10, "--threshold", help="Minimum evidence threshold"),
    dominance: float = typer.Option(0.6, "--dominance", help="Dominance threshold 0.0-1.0"),
    limit: int = typer.Option(20, "--limit", help="Max suggestions to show"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Mine rule suggestions from high-confidence keyword patterns."""
    mining.handle(fy, person, search, show_unlabeled, threshold, dominance, limit, base_dir)


@app.command(name="metrics")
def cmd_metrics(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Calculate coverage & household metrics."""
    metrics.handle(fy, person, base_dir)


@app.command(name="optimize")
def cmd_optimize(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    persons: str = typer.Option(..., "--persons", help="Comma-separated person names"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Optimize deduction allocation across persons to minimize tax liability."""
    optimize.handle(fy, persons, base_dir)


@app.command(name="property")
def cmd_property(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    person: str = typer.Option(..., "--person", help="Person name"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Aggregate property expenses (rent, water, council, strata)."""
    property.handle(fy, person, base_dir)


@app.command(name="gains-plan")
def cmd_gains_plan(
    projection: str = typer.Option(..., "--projection", help="Tax projection: 25:30%,26:45%"),
    gains: list[float] = typer.Option(None, "--gains", help="Gains (repeatable)"),
    losses: list[float] = typer.Option(None, "--losses", help="Losses (repeatable)"),
):
    """Plan multi-year gains realization with loss carryforward."""
    gains.handle(projection, gains, losses)


def main():
    """Entry point for tax CLI."""
    app()
