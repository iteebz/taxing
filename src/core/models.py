from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal, Protocol


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
        if not isinstance(self.personal_pct, Decimal):
            object.__setattr__(self, "personal_pct", Decimal(str(self.personal_pct)))
        if self.personal_pct < 0 or self.personal_pct > 1:
            raise ValueError(f"personal_pct must be 0.0-1.0, got {self.personal_pct}")
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
        if not isinstance(self.deductible_pct, Decimal):
            object.__setattr__(self, "deductible_pct", Decimal(str(self.deductible_pct)))
        if self.deductible_pct < 0 or self.deductible_pct > 1:
            raise ValueError(f"deductible_pct must be 0.0-1.0, got {self.deductible_pct}")

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
        if not isinstance(self.occupancy_pct, Decimal):
            object.__setattr__(self, "occupancy_pct", Decimal(str(self.occupancy_pct)))
        if self.occupancy_pct < 0 or self.occupancy_pct > 1:
            raise ValueError(f"occupancy_pct must be 0.0-1.0, got {self.occupancy_pct}")

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
