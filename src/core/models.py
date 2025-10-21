from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import NewType, Protocol

Currency = NewType("Currency", str)
AUD = Currency("AUD")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: float) -> "Money":
        return Money(self.amount * Decimal(str(scalar)), self.currency)

    def __rmul__(self, scalar: float) -> "Money":
        return self.__mul__(scalar)


@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Money
    description: str
    source_bank: str
    source_person: str
    category: set[str] | None = None
    is_transfer: bool = False
    claimant: str | None = None
    sources: frozenset[str] = None
    source_txn_ids: tuple[str, ...] = field(default_factory=tuple)
    personal_pct: Decimal = Decimal("0")

    def __post_init__(self):
        if self.sources is None:
            object.__setattr__(self, "sources", frozenset({self.source_bank}))
        if not isinstance(self.personal_pct, Decimal):
            object.__setattr__(self, "personal_pct", Decimal(str(self.personal_pct)))
        if self.personal_pct < 0 or self.personal_pct > 1:
            raise ValueError(f"personal_pct must be 0.0-1.0, got {self.personal_pct}")


@dataclass(frozen=True)
class Trade:
    date: date
    code: str
    action: str
    units: Decimal
    price: Money
    fee: Money
    source_person: str


@dataclass(frozen=True)
class Gain:
    fy: int
    raw_profit: Money
    taxable_gain: Money
    action: str


@dataclass(frozen=True)
class Deduction:
    category: str
    amount: Money
    rate: Decimal
    rate_basis: str
    fy: int


@dataclass(frozen=True)
class Summary:
    category: str
    credit_amount: Decimal
    debit_amount: Decimal


@dataclass(frozen=True)
class PropertyExpense:
    expense_type: str
    amount: Money


@dataclass(frozen=True)
class PropertyExpensesSummary:
    rent: Money
    water: Money
    council: Money
    strata: Money

    @property
    def total(self) -> Money:
        return self.rent + self.water + self.council + self.strata


@dataclass(frozen=True)
class Holding:
    ticker: str
    units: Decimal
    cost_basis: Money
    current_price: Money

    @property
    def current_value(self) -> Money:
        return Money(
            self.units * self.current_price.amount,
            self.current_price.currency,
        )

    @property
    def unrealized_gain(self) -> Money:
        return self.current_value - self.cost_basis


@dataclass(frozen=True)
class Loss:
    fy: int
    amount: Money
    source_fy: int


@dataclass(frozen=True)
class Asset:
    fy: int
    description: str
    cost: Money
    life_years: int
    depreciation_method: str = "PC"


@dataclass(frozen=True)
class Rent:
    date: date
    amount: Money
    tenant: str
    fy: int


@dataclass(frozen=True)
class Water:
    date: date
    amount: Money
    fy: int


@dataclass(frozen=True)
class Council:
    date: date
    amount: Money
    fy: int


@dataclass(frozen=True)
class Strata:
    date: date
    amount: Money
    fy: int


@dataclass(frozen=True)
class CapitalWorks:
    date: date
    amount: Money
    description: str
    life_years: int
    asset_id: str
    fy: int


@dataclass(frozen=True)
class Interest:
    date: date
    amount: Money
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
    def total_rental_income(self) -> Money:
        if not self.rents:
            return Money(Decimal("0"), AUD)
        return sum((r.amount for r in self.rents), Money(Decimal("0"), AUD))

    @property
    def total_expenses(self) -> Money:
        items = self.waters + self.councils + self.stratas
        if not items:
            return Money(Decimal("0"), AUD)
        return sum((i.amount for i in items), Money(Decimal("0"), AUD))

    @property
    def deductible_expenses(self) -> Money:
        return self.total_expenses * self.occupancy_pct

    @property
    def net_rental_income(self) -> Money:
        return self.total_rental_income - self.deductible_expenses


@dataclass(frozen=True)
class Individual:
    name: str
    fy: int
    income: Money
    deductions: list[Money] = field(default_factory=list)
    gains: list[Gain] = field(default_factory=list)
    losses: list[Loss] = field(default_factory=list)

    @property
    def total_deductions(self) -> Money:
        if not self.deductions:
            return Money(Decimal("0"), AUD)
        return sum(self.deductions, Money(Decimal("0"), AUD))

    @property
    def total_gains(self) -> Money:
        if not self.gains:
            return Money(Decimal("0"), AUD)
        return sum((g.taxable_gain for g in self.gains), Money(Decimal("0"), AUD))

    @property
    def total_losses(self) -> Money:
        if not self.losses:
            return Money(Decimal("0"), AUD)
        return sum((loss.amount for loss in self.losses), Money(Decimal("0"), AUD))

    @property
    def taxable_income(self) -> Money:
        return self.income + self.total_gains - self.total_deductions - self.total_losses


class Classifier(Protocol):
    def classify(self, description: str) -> set[str]: ...


class Deducer(Protocol):
    def deduce(self, txns: list[Transaction], weights: dict[str, float]) -> dict[str, Money]: ...
