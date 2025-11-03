import json
from decimal import Decimal
from pathlib import Path

import typer

from src.core.household import _tax_liability, optimize_household
from src.core.metrics import coverage as calc_coverage
from src.core.mining import MiningConfig, mine_suggestions, score_suggestions
from src.core.models import Individual, Transaction
from src.core.rules import load_rules
from src.core.classify import classify
from src.io.persist import dicts_from_csv, from_csv
from src.lib.search import load_cache, search_description
from src.pipeline import run as run_pipeline

app = typer.Typer(
    name="tax",
    help="Tax optimization and management tool",
    no_args_is_help=False,
)


def _load_txns_all_years(base_dir: Path, person: str | None = None) -> list[Transaction]:
    """Load and re-classify transactions from ALL FY directories."""
    from dataclasses import replace
    from src.io import ingest_all_years
    from src.core.dedupe import dedupe
    from src.core.transfers import is_transfer
    
    txns = ingest_all_years(base_dir, persons=[person] if person else None)
    txns = dedupe(txns)
    rules = load_rules(base_dir)
    
    txns_classified = [
        replace(
            t,
            cats=(cat := classify(t.description, rules)),
            is_transfer=is_transfer(replace(t, cats=cat)),
        )
        for t in txns
    ]
    
    return txns_classified


def _load_employment_income(base_dir: Path, fy: int) -> dict[str, Decimal]:
    """Load employment income per person from config file."""
    config_file = base_dir / f"employment_income_fy{fy}.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"Missing employment income config: {config_file}\n"
            'Expected format: {{"alice": 150000, "bob": 50000}}'
        )

    with open(config_file) as f:
        data = json.load(f)

    return {k: Decimal(str(v)) for k, v in data.items()}


def _load_deductions(base_dir: Path, fy: int, person: str) -> Decimal:
    """Load total deductions for a person from Phase 1 output."""
    deductions_file = base_dir / "data" / f"fy{fy}" / person / "data" / "deductions.csv"
    if not deductions_file.exists():
        return Decimal("0")

    data = dicts_from_csv(deductions_file)
    total = Decimal("0")
    for row in data:
        if "amount" in row:
            total += Decimal(str(row["amount"]))

    return total


@app.command(name="run")
def cmd_run(
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Run full tax pipeline (ingest all years → classify → deduce → trades → persist)."""
    base_dir = Path(base_dir or ".")
    result = run_pipeline(base_dir)

    print("\nPipeline Results (All Years)")
    print("-" * 70)

    for person in sorted(result.keys()):
        data = result[person]
        print(
            f"{person:<20} txns={data['txn_count']:<5} "
            f"classified={data['classified_count']:<5} "
            f"deductions={len(data['deductions']):<5} "
            f"gains={data['gains_count']}"
        )

    print("-" * 70)


@app.command(name="coverage")
def cmd_coverage(
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    sample: int = typer.Option(None, "--sample", help="Sample N uncategorized transactions"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Show classification coverage gaps across all fiscal years."""
    import random

    base_dir = Path(base_dir or ".")
    txns = _load_txns_all_years(base_dir, person)

    if not txns:
        print("\nNo transactions found")
        return

    cov = calc_coverage(txns)
    print("\nClassification Coverage (All Years)")
    print("-" * 70)
    print(
        f"Transactions Categorized:     {cov['pct_txns']:>6.1f}% ({cov['count_labeled']}/{cov['count_total']})"
    )
    print(
        f"Outbound Spending Categorized: {cov['pct_debit']:>6.1f}% (${cov['debit_labeled']:>12,.0f}/${cov['debit_total']:>12,.0f})"
    )
    print(
        f"Inbound Income Categorized:    {cov['pct_credit']:>6.1f}% (${cov['credit_labeled']:>12,.0f}/${cov['credit_total']:>12,.0f})"
    )

    if sample:
        uncategorized = [t for t in txns if not t.cats and t.amount is not None]
        if uncategorized:
            sample_txns = random.sample(uncategorized, min(sample, len(uncategorized)))
            sample_txns = sorted(sample_txns, key=lambda x: float(abs(x.amount)), reverse=True)
            print(f"\nUncategorized Sample ({len(sample_txns)} of {len(uncategorized)})")
            print("-" * 70)
            for t in sample_txns:
                print(f"{t.date} | {t.amount:>10.2f} | {t.description[:55]}")
        else:
            print("\nNo uncategorized transactions")


@app.command(name="mine")
def cmd_mine(
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    search: bool = typer.Option(False, "--search", help="Enable search for categorization hints"),
    batch_start: int = typer.Option(0, "--batch-start", help="Start index for batch processing"),
    batch_size: int = typer.Option(20, "--batch-size", help="Number of txns per batch"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Review uncategorized transactions (sorted by spend) with optional search."""
    base_dir = Path(base_dir or ".")
    txns = _load_txns_all_years(base_dir, person)

    if not txns:
        print("\nNo transactions found")
        return

    unlabeled = [t for t in txns if not t.cats]

    if not unlabeled:
        print("All transactions categorized!")
        return

    cache_path = base_dir / ".search_cache.json" if search else None
    cache = load_cache(cache_path) if search else {}
    
    unlabeled_sorted = sorted(unlabeled, key=lambda t: float(abs(t.amount)) if t.amount else 0, reverse=True)
    batch = unlabeled_sorted[batch_start : batch_start + batch_size]
    
    for i, txn in enumerate(batch, batch_start + 1):
        amt_str = f"${txn.amount:>10.2f}" if txn.amount is not None else "$      None"
        print(f"{i}. {txn.description} | {txn.date} | {amt_str}")
        
        if search:
            results = search_description(txn.description, cache, cache_path, max_results=2)
            if results:
                for result in results:
                    if isinstance(result, dict):
                        title = result.get('title', '')[:80]
                        print(f"   → {title}")
    
    if batch_start + batch_size < len(unlabeled_sorted):
        print(f"\nNext: --batch-start {batch_start + batch_size}")


@app.command(name="classify")
def cmd_classify(
    description: str = typer.Argument(..., help="Transaction description to classify"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Classify a single transaction description."""
    base_dir = Path(base_dir or ".")
    rules = load_rules(base_dir)
    
    result = classify(description, rules)
    
    print(f"\nDescription: {description}")
    print(f"Matches: {sorted(result) if result else 'None'}")
    
    if not result:
        print("\nDebug info:")
        desc_upper = description.strip().upper()
        print(f"  Normalized: {desc_upper}")
        for category, keywords in sorted(rules.items()):
            matches = [kw for kw in keywords if kw in desc_upper]
            if matches:
                print(f"  {category}: {matches}")


@app.command(name="optimize")
def cmd_optimize(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    persons: str = typer.Option(..., "--persons", help="Comma-separated person names"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Optimize deduction allocation across persons to minimize tax liability."""
    base_dir = Path(base_dir or ".")
    persons_list = [p.strip() for p in persons.split(",") if p.strip()]

    if not persons_list:
        raise typer.BadParameter("--persons required (comma-separated list)")

    employment_income = _load_employment_income(base_dir, fy)

    missing = set(persons_list) - set(employment_income.keys())
    if missing:
        raise typer.BadParameter(f"Missing employment income for: {missing}")

    individuals = {}
    total_deductions = Decimal("0")

    for person in persons_list:
        emp_income = employment_income[person]
        deductions = _load_deductions(base_dir, fy, person)
        total_deductions += deductions

        individuals[person] = Individual(
            name=person,
            fy=fy,
            income=emp_income,
            deductions=[deductions] if deductions > 0 else [],
        )

    person_list = sorted(individuals.keys())

    print(f"\n{'Person':<20} {'Income':<18} {'Deductions':<18} {'Tax':<15}")
    print("-" * 75)

    if len(individuals) == 2:
        result = optimize_household(individuals[person_list[0]], individuals[person_list[1]])
        yours_income = individuals[person_list[0]].income
        janice_income = individuals[person_list[1]].income
        yours_deductions = result.yours.total_deductions
        janice_deductions = result.janice.total_deductions
        yours_tax = result.your_liability.total
        janice_tax = result.janice_liability.total

        print(
            f"{person_list[0]:<20} ${yours_income:<17,.0f} ${yours_deductions:<17,.0f} ${yours_tax:<14,.0f}"
        )
        print(
            f"{person_list[1]:<20} ${janice_income:<17,.0f} ${janice_deductions:<17,.0f} ${janice_tax:<14,.0f}"
        )
        total_tax = yours_tax + janice_tax
    else:
        total_tax = Decimal("0")
        for person in person_list:
            ind = individuals[person]
            deductions_sum = sum(ind.deductions) if ind.deductions else Decimal("0")
            taxable = ind.income - deductions_sum
            liability = _tax_liability(
                taxable,
                ind.fy,
                medicare_status="single",
                has_private_health_cover=ind.has_private_health_cover,
            )
            total_tax += liability.total

            print(
                f"{person:<20} ${ind.income:<17,.0f} ${deductions_sum:<17,.0f} ${liability.total:<14,.0f}"
            )

    print("-" * 75)
    print(f"{'TOTAL':<20} {'':<18} ${total_deductions:<17,.0f} ${total_tax:<14,.0f}")


def main():
    """Entry point for tax CLI."""
    app()


if __name__ == "__main__":
    main()
