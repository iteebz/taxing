import json
from decimal import Decimal
from pathlib import Path

import typer

from src.core.household import _tax_liability, optimize_household
from src.core.models import Individual
from src.io.persist import dicts_from_csv


def load_employment_income(base_dir: Path, fy: int) -> dict[str, Decimal]:
    """Load employment income per person from config file."""
    config_file = base_dir / f"employment_income_fy{fy}.json"
    if not config_file.exists():
        raise FileNotFoundError(
            f"Missing employment income config: {config_file}\n"
            'Expected format: {"alice": 150000, "bob": 50000}'
        )

    with open(config_file) as f:
        data = json.load(f)

    return {k: Decimal(str(v)) for k, v in data.items()}


def load_deductions(base_dir: Path, fy: int, person: str) -> list[Decimal]:
    """Load deductions for a person from Phase 1 output."""
    deductions_file = base_dir / "data" / f"fy{fy}" / person / "data" / "deductions.csv"
    if not deductions_file.exists():
        return []

    data = dicts_from_csv(deductions_file)
    total = Decimal("0")
    for row in data:
        if "amount" in row:
            total += Decimal(str(row["amount"]))

    return [total] if total > 0 else []


def handle(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    persons: str = typer.Option(..., "--persons", help="Comma-separated person names"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Optimize deduction allocation across persons to minimize tax liability."""
    base_dir = Path(base_dir or ".")
    persons_list = persons.split(",") if persons else []

    if not persons_list:
        raise typer.BadParameter("--persons required (comma-separated list)")

    employment_income = load_employment_income(base_dir, fy)

    missing = set(persons_list) - set(employment_income.keys())
    if missing:
        raise typer.BadParameter(f"Missing employment income for: {missing}")

    individuals = {}
    all_deductions = []

    for person in persons_list:
        emp_income = employment_income[person]
        deductions = load_deductions(base_dir, fy, person)
        all_deductions.extend(deductions)

        individuals[person] = Individual(
            name=person,
            fy=fy,
            income=emp_income,
            deductions=deductions,
        )

    person_list = sorted(individuals.keys())

    if len(individuals) == 1:
        ind = individuals[person_list[0]]
        print(f"\n{'Person':<15} {'Income':<15} {'Deductions':<15} {'Tax':<12}")
        print("-" * 60)
        total_deductions = sum(all_deductions)
        taxable = ind.income - total_deductions
        liability = _tax_liability(
            taxable,
            ind.fy,
            medicare_status="single",
            has_private_health_cover=ind.has_private_health_cover,
        )
        print(
            f"{person_list[0]:<15} "
            f"${ind.income:<14,.0f} "
            f"${total_deductions:<14,.0f} "
            f"${liability.total:<11,.0f} "
        )
        print("-" * 60)
        print(f"{'TOTAL':<15} {'':<15} ${total_deductions:<14,.0f} ${liability.total:<11,.0f}")
    elif len(individuals) == 2:
        result = optimize_household(individuals[person_list[0]], individuals[person_list[1]])

        yours_income = individuals[person_list[0]].income
        janice_income = individuals[person_list[1]].income
        yours_deductions = result.yours.total_deductions
        janice_deductions = result.janice.total_deductions
        yours_tax = result.your_liability.total
        janice_tax = result.janice_liability.total

        print(f"\n{'Person':<15} {'Income':<15} {'Deductions':<15} {'Tax':<12} {'Savings':<12}")
        print("-" * 75)

        print(
            f"{person_list[0]:<15} "
            f"${yours_income:<14,.0f} "
            f"${yours_deductions:<14,.0f} "
            f"${yours_tax:<11,.0f} "
        )
        print(
            f"{person_list[1]:<15} "
            f"${janice_income:<14,.0f} "
            f"${janice_deductions:<14,.0f} "
            f"${janice_tax:<11,.0f} "
        )
        print("-" * 75)
        total_deductions = sum(all_deductions)
        total_tax = yours_tax + janice_tax
        print(f"{'TOTAL':<15} {'':<15} ${total_deductions:<14,.0f} ${total_tax:<11,.0f}")
    else:
        print(f"\n{'Person':<15} {'Income':<15} {'Deductions':<15} {'Tax':<12}")
        print("-" * 60)

        total_deductions = sum(all_deductions)
        total_tax = Decimal("0")

        for person in person_list:
            ind = individuals[person]
            taxable = ind.income - (sum(ind.deductions) if ind.deductions else Decimal("0"))
            liability = _tax_liability(
                taxable,
                ind.fy,
                medicare_status="single",
                has_private_health_cover=ind.has_private_health_cover,
            )
            total_tax += liability.total

            deductions_sum = sum(ind.deductions) if ind.deductions else Decimal("0")
            print(
                f"{person:<15} "
                f"${ind.income:<14,.0f} "
                f"${deductions_sum:<14,.0f} "
                f"${liability.total:<11,.0f} "
            )

        print("-" * 60)
        print(f"{'TOTAL':<15} {'':<15} ${total_deductions:<14,.0f} ${total_tax:<11,.0f}")
