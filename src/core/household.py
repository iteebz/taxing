from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from typing import Literal

from src.core.config import Bracket, FYConfig, MedicareConfig, load_config
from src.core.models import Individual


@dataclass(frozen=True)
class Liability:
    income_tax: Decimal
    medicare_levy: Decimal
    medicare_surcharge: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return self.income_tax + self.medicare_levy + self.medicare_surcharge


@dataclass(frozen=True)
class Allocation:
    yours: Individual
    janice: Individual
    your_liability: Liability
    janice_liability: Liability

    @property
    def total(self) -> Decimal:
        return self.your_liability.total + self.janice_liability.total


@dataclass(frozen=True)
class TaxResult:
    individual: Individual
    liability: Liability


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _effective_income(amount: Decimal) -> Decimal:
    return max(amount, Decimal("0"))


def _income_tax(amount: Decimal, brackets: Sequence[Bracket]) -> Decimal:
    taxable = _effective_income(amount)
    tax = Decimal("0")
    for bracket in brackets:
        lower_threshold = Decimal(bracket.from_val - 1)
        upper_threshold = Decimal(bracket.to_val)
        if taxable <= lower_threshold:
            continue
        taxable_portion = min(taxable, upper_threshold) - lower_threshold
        if taxable_portion <= 0:
            continue
        tax += taxable_portion * bracket.rate
    return tax


def _medicare_levy_single(
    taxable_amount: Decimal,
    medicare: MedicareConfig,
) -> Decimal:
    taxable = _effective_income(taxable_amount)
    if taxable == 0:
        return Decimal("0")

    threshold = Decimal(medicare.low_income_threshold_single)
    if taxable <= threshold:
        return Decimal("0")

    full_levy = taxable * medicare.base_rate
    reduction = (taxable - threshold) * medicare.phase_in_rate_single
    if reduction <= 0:
        return Decimal("0")
    return min(full_levy, reduction)


def _medicare_levy_family(
    individual_amount: Decimal,
    family_income: Decimal,
    dependents: int,
    medicare: MedicareConfig,
) -> Decimal:
    if family_income <= 0:
        return Decimal("0")

    threshold = Decimal(medicare.low_income_threshold_family) + Decimal(
        medicare.dependent_increment * dependents
    )
    if family_income <= threshold:
        return Decimal("0")

    full_family_levy = family_income * medicare.base_rate
    reduction = (family_income - threshold) * medicare.phase_in_rate_family
    family_levy = min(full_family_levy, reduction) if reduction > 0 else full_family_levy

    individual_share = Decimal("0") if family_income == 0 else individual_amount / family_income
    individual_full_levy = _effective_income(individual_amount) * medicare.base_rate
    calculated_share = family_levy * individual_share
    return min(individual_full_levy, calculated_share)


def _surcharge_rate(
    taxable_amount: Decimal,
    medicare: MedicareConfig,
    status: Literal["single", "family"],
    dependents: int,
) -> Decimal:
    surcharge = medicare.surcharge
    if surcharge is None:
        return Decimal("0")

    tiers = surcharge.single if status == "single" else surcharge.family
    if not tiers:
        return Decimal("0")

    adjustment = Decimal("0")
    if status == "family":
        adjustment = Decimal(surcharge.dependent_increment * dependents)

    applicable_rate = Decimal("0")
    for tier in tiers:
        threshold = Decimal(tier.threshold) + adjustment
        if taxable_amount > threshold:
            applicable_rate = tier.rate
        else:
            break
    return applicable_rate


def _medicare_surcharge_amount(
    taxable_amount: Decimal,
    medicare: MedicareConfig,
    status: Literal["single", "family"],
    dependents: int,
    has_private_health_cover: bool,
    surcharge_income: Decimal,
) -> Decimal:
    if has_private_health_cover:
        return Decimal("0")
    rate = _surcharge_rate(surcharge_income, medicare, status, dependents)
    if rate == 0:
        return Decimal("0")
    return _effective_income(taxable_amount) * rate


def _resolve_fy_key(fy: int) -> int:
    return fy if fy >= 1900 else 2000 + fy


@lru_cache(maxsize=16)
def _load_config(fy: int) -> FYConfig:
    return load_config(_resolve_fy_key(fy))


def _tax_liability(
    taxable_income: Decimal,
    fy: int,
    *,
    medicare_status: Literal["single", "family"] = "single",
    medicare_dependents: int = 0,
    has_private_health_cover: bool = True,
    family_taxable_income: Decimal | None = None,
    family_dependents: int = 0,
) -> Liability:
    config = _load_config(fy)

    taxable_amount = _effective_income(taxable_income)
    income_tax = _income_tax(taxable_amount, config.brackets)

    medicare = config.medicare
    if medicare_status == "family":
        combined = family_taxable_income if family_taxable_income is not None else taxable_amount
        levy = _medicare_levy_family(
            taxable_amount,
            combined,
            family_dependents,
            medicare,
        )
        surcharge_base = combined
    else:
        levy = _medicare_levy_single(taxable_amount, medicare)
        surcharge_base = taxable_amount

    surcharge = _medicare_surcharge_amount(
        taxable_amount,
        medicare,
        medicare_status,
        medicare_dependents if medicare_status == "single" else family_dependents,
        has_private_health_cover,
        surcharge_base,
    )

    return Liability(
        income_tax=_quantize(income_tax),
        medicare_levy=_quantize(levy),
        medicare_surcharge=_quantize(surcharge),
    )


def _evaluate_allocation(
    yours: Individual,
    janice: Individual,
    yours_deductions: Sequence[Decimal],
    janice_deductions: Sequence[Decimal],
) -> Allocation:
    updated_yours = replace(yours, deductions=list(yours_deductions), medicare_status="family")
    updated_janice = replace(janice, deductions=list(janice_deductions), medicare_status="family")

    your_taxable = updated_yours.taxable_income
    janice_taxable = updated_janice.taxable_income

    family_income = your_taxable + janice_taxable
    family_dependents = updated_yours.medicare_dependents + updated_janice.medicare_dependents

    your_liability = _tax_liability(
        your_taxable,
        updated_yours.fy,
        medicare_status="family",
        medicare_dependents=updated_yours.medicare_dependents,
        has_private_health_cover=updated_yours.has_private_health_cover,
        family_taxable_income=family_income,
        family_dependents=family_dependents,
    )
    janice_liability = _tax_liability(
        janice_taxable,
        updated_janice.fy,
        medicare_status="family",
        medicare_dependents=updated_janice.medicare_dependents,
        has_private_health_cover=updated_janice.has_private_health_cover,
        family_taxable_income=family_income,
        family_dependents=family_dependents,
    )

    return Allocation(
        yours=updated_yours,
        janice=updated_janice,
        your_liability=your_liability,
        janice_liability=janice_liability,
    )


def _combine_deductions(yours: Individual, janice: Individual) -> Sequence[Decimal]:
    return tuple(yours.deductions + janice.deductions)


def _iter_allocations(
    deductions: Sequence[Decimal],
) -> Iterable[tuple[Sequence[Decimal], Sequence[Decimal]]]:
    n = len(deductions)
    for i in range(1 << n):
        yours_alloc = []
        janice_alloc = []
        for j in range(n):
            if (i >> j) & 1:
                yours_alloc.append(deductions[j])
            else:
                janice_alloc.append(deductions[j])
        yield tuple(yours_alloc), tuple(janice_alloc)


def allocate_deductions(
    yours_income: Decimal,
    janice_income: Decimal,
    shared_deductions: list[Decimal],
    fy: int,
) -> tuple[Decimal, Decimal]:
    yours = Individual(
        name="yours",
        fy=fy,
        income=yours_income,
        deductions=shared_deductions,
    )
    janice = Individual(
        name="janice",
        fy=fy,
        income=janice_income,
    )
    allocation = optimize_household(yours, janice)
    return (
        allocation.yours.total_deductions,
        allocation.janice.total_deductions,
    )


def calculate_tax(individual: Individual) -> TaxResult:
    """Calculate single person's tax liability.

    Args:
        individual: Person with income, deductions, and tax attributes

    Returns:
        TaxResult with calculated liability
    """
    taxable = individual.taxable_income
    liability = _tax_liability(
        taxable,
        individual.fy,
        medicare_status="single",
        has_private_health_cover=individual.has_private_health_cover,
    )
    return TaxResult(individual=individual, liability=liability)


def optimize_household(yours: Individual, janice: Individual) -> Allocation:
    """Optimize deduction allocation for 2-person household.

    Exhaustively searches all deduction allocations to minimize total tax liability.
    Current implementation is hardcoded for exactly 2 people.
    """
    deductions = _combine_deductions(yours, janice)
    best_allocation: Allocation | None = None
    best_total: Decimal | None = None

    for yours_alloc, janice_alloc in _iter_allocations(deductions):
        allocation = _evaluate_allocation(yours, janice, yours_alloc, janice_alloc)
        total = allocation.total
        if best_total is None or total < best_total:
            best_total = total
            best_allocation = allocation

    if best_allocation is None:
        # No deductions to allocate, still compute baseline liabilities.
        best_allocation = _evaluate_allocation(yours, janice, (), ())

    return best_allocation
