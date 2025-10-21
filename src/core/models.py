from dataclasses import dataclass
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
    source_txn_ids: tuple[str, ...] = None

    def __post_init__(self):
        if self.sources is None:
            object.__setattr__(self, "sources", frozenset({self.source_bank}))
        if self.source_txn_ids is None:
            object.__setattr__(self, "source_txn_ids", ())


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
    amount: Decimal


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


class Classifier(Protocol):
    def classify(self, description: str) -> set[str]: ...


class Deducer(Protocol):
    def deduce(self, txns: list[Transaction], weights: dict[str, float]) -> dict[str, Money]: ...
