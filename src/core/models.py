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


class Classifier(Protocol):
    def classify(self, description: str) -> set[str]: ...


class Deducer(Protocol):
    def deduce(self, txns: list[Transaction], weights: dict[str, float]) -> dict[str, Money]: ...
