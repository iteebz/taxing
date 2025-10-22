from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal, Protocol


def _validate_pct_field(name: str, value) -> Decimal:
    """Validate and coerce percentage field to Decimal in range [0, 1]."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be 0.0-1.0, got {value}")
    return value


@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Decimal
    description: str
    bank: str
    individual: str
    category: set[str] | None = None
    is_transfer: bool = False
    claimant: str | None = None
    sources: frozenset[str] = None
    source_txn_ids: tuple[str, ...] = field(default_factory=tuple)
    personal_pct: Decimal = Decimal("0")
    confidence: float = 1.0
    account: str | None = None

    def __post_init__(self):
        if self.sources is None:
            object.__setattr__(self, "sources", frozenset({self.bank}))
        pct = _validate_pct_field("personal_pct", self.personal_pct)
        object.__setattr__(self, "personal_pct", pct)
        if not isinstance(self.confidence, float) or self.confidence < 0 or self.confidence > 1:
            raise ValueError(f"confidence must be 0.0-1.0, got {self.confidence}")


@dataclass(frozen=True)
class Trade:
    date: date
    code: str
    action: str
    units: Decimal
    price: Decimal
    fee: Decimal
    individual: str


@dataclass(frozen=True)
class Gain:
    fy: int
    raw_profit: Decimal
    taxable_gain: Decimal


@dataclass(frozen=True)
class Deduction:
    category: str
    amount: Decimal
    rate: Decimal
    rate_basis: str
    fy: int


@dataclass(frozen=True)
class Car:
    total_spend: Decimal
    deductible_pct: Decimal

    def __post_init__(self):
        pct = _validate_pct_field("deductible_pct", self.deductible_pct)
        object.__setattr__(self, "deductible_pct", pct)

    @property
    def implied_km(self) -> Decimal:
        return (self.total_spend * self.deductible_pct) / Decimal("0.67")

    @property
    def deductible_amount(self) -> Decimal:
        return self.implied_km * Decimal("0.67")


@dataclass(frozen=True)
class Summary:
    category: str
    credit_amount: Decimal
    debit_amount: Decimal

    @classmethod
    def from_transactions(cls, txns: list["Transaction"]) -> list["Summary"]:
        """Aggregate transactions into summaries by category.

        Filters out transfers and transactions without categories.
        Sums credit (positive) and debit (negative) amounts separately.
        """
        summary_dict = {}
        for t in txns:
            if t.category and not t.is_transfer and t.amount is not None and not t.amount.is_nan():
                for cat in t.category:
                    if cat not in summary_dict:
                        summary_dict[cat] = (Decimal(0), Decimal(0))
                    credit, debit = summary_dict[cat]
                    amt = t.amount
                    if amt > 0:
                        summary_dict[cat] = (credit + amt, debit)
                    else:
                        summary_dict[cat] = (credit, debit + abs(amt))

        return [cls(cat, credit, debit) for cat, (credit, debit) in summary_dict.items()]


@dataclass(frozen=True)
class PropertyExpense:
    expense_type: str
    amount: Decimal


@dataclass(frozen=True)
class PropertyExpensesSummary:
    rent: Decimal
    water: Decimal
    council: Decimal
    strata: Decimal

    @property
    def total(self) -> Decimal:
        return self.rent + self.water + self.council + self.strata


@dataclass(frozen=True)
class Position:
    ticker: str
    units: Decimal
    total_cost_basis: Decimal


@dataclass(frozen=True)
class Loss:
    fy: int
    amount: Decimal
    source_fy: int


@dataclass(frozen=True)
class Asset:
    fy: int
    description: str
    cost: Decimal
    life_years: int
    depreciation_method: str = "PC"
    purchase_date: date | None = None


@dataclass(frozen=True)
class Rent:
    date: date
    amount: Decimal
    tenant: str
    fy: int


@dataclass(frozen=True)
class Water:
    date: date
    amount: Decimal
    fy: int


@dataclass(frozen=True)
class Council:
    date: date
    amount: Decimal
    fy: int


@dataclass(frozen=True)
class Strata:
    date: date
    amount: Decimal
    fy: int


@dataclass(frozen=True)
class CapitalWorks:
    date: date
    amount: Decimal
    description: str
    life_years: int
    asset_id: str
    fy: int


@dataclass(frozen=True)
class Interest:
    date: date
    amount: Decimal
    loan_id: str
    fy: int


@dataclass(frozen=True)
class Property:
    address: str
    owner: str
    fy: int
    occupancy_pct: Decimal
    rents: list[Rent] = field(default_factory=list)
    waters: list[Water] = field(default_factory=list)
    councils: list[Council] = field(default_factory=list)
    stratas: list[Strata] = field(default_factory=list)
    capital_works: list[CapitalWorks] = field(default_factory=list)
    interests: list[Interest] = field(default_factory=list)

    def __post_init__(self):
        pct = _validate_pct_field("occupancy_pct", self.occupancy_pct)
        object.__setattr__(self, "occupancy_pct", pct)

    @property
    def total_rental_income(self) -> Decimal:
        if not self.rents:
            return Decimal("0")
        return sum((r.amount for r in self.rents), Decimal("0"))

    @property
    def total_expenses(self) -> Decimal:
        items = self.waters + self.councils + self.stratas
        if not items:
            return Decimal("0")
        return sum((i.amount for i in items), Decimal("0"))

    @property
    def deductible_expenses(self) -> Decimal:
        return self.total_expenses * self.occupancy_pct

    @property
    def net_rental_income(self) -> Decimal:
        return self.total_rental_income - self.deductible_expenses


@dataclass(frozen=True)
class Individual:
    name: str
    fy: int
    income: Decimal
    deductions: list[Decimal] = field(default_factory=list)
    gains: list[Gain] = field(default_factory=list)
    medicare_status: Literal["single", "family"] = "single"
    medicare_dependents: int = 0
    has_private_health_cover: bool = True

    @property
    def total_deductions(self) -> Decimal:
        if not self.deductions:
            return Decimal("0")
        return sum(self.deductions, Decimal("0"))

    @property
    def total_gains(self) -> Decimal:
        if not self.gains:
            return Decimal("0")
        return sum((g.taxable_gain for g in self.gains), Decimal("0"))

    @property
    def taxable_income(self) -> Decimal:
        return self.income + self.total_gains - self.total_deductions


class Classifier(Protocol):
    def classify(self, description: str) -> set[str]: ...


class Deducer(Protocol):
    def deduce(
        self,
        txns: list[Transaction],
        fy: int,
        conservative: bool = False,
        weights: dict[str, float] | None = None,
    ) -> list[Deduction]: ...
