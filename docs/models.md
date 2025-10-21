# core models reference

All domain objects are frozen dataclasses (immutable, hashable, type-safe).

## money & currency

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal       # Precise, no float rounding
    currency: Currency    # NewType("Currency", str) → "AUD"
    
    # Operators (type-safe)
    def __add__(self, other: Money) -> Money:        # Raises if currencies differ
    def __sub__(self, other: Money) -> Money:        # Raises if currencies differ
    def __mul__(self, scalar: float) -> Money:       # Money * 0.5
```

**Why Decimal?** Prevents silent rounding errors. `0.1 + 0.2 ≠ 0.3` in float.

**Why NewType Currency?** Prevents `Money(100, "USD") + Money(100, "AUD")` → type error at development time.

---

## transactions & classification

```python
@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Money
    description: str
    source_bank: str              # "ANZ", "CBA", "Beem", "Wise"
    source_person: str            # "tyson", "janice"
    category: set[str] | None     # {"groceries", "transport"} or None (unclassified)
    is_transfer: bool = False     # Cross-ledger or P2P transfer
    claimant: str | None = None   # Person claiming the deduction
    sources: frozenset[str]       # Ledger sources (transfer reconciliation)
    source_txn_ids: tuple[str]    # Audit trail for deduplication
    personal_pct: Decimal         # Split ratio (0.0-1.0) for shared txns
```

**Classification**: External rules (src/core/rules.py) map keywords to categories.
- Case-insensitive substring matching
- Multi-category support (one txn → multiple deduction categories)
- Immutable after creation (no post-hoc mutations)

**Transfers & Deduplication**:
- `is_transfer` flag identifies cross-ledger moves
- `sources` tracks origin ledgers (Beemit credit → debit reconciliation)
- `source_txn_ids` provides audit trail (link to original rows)

---

## gains, losses & capital events

```python
@dataclass(frozen=True)
class Trade:
    date: date
    code: str                     # "ASX:BHP", "CRYPTO:BTC"
    action: str                   # "buy" or "sell"
    units: Decimal
    price: Money                  # Per-unit price
    fee: Money
    source_person: str

@dataclass(frozen=True)
class Gain:
    fy: int                       # Financial year (25 = FY2024-25)
    raw_profit: Money             # Before CGT discount
    taxable_gain: Money           # After 50% discount if held >365 days
    action: str                   # "loss" | "discount" | "fifo" (priority fired)

@dataclass(frozen=True)
class Loss:
    fy: int
    amount: Money                 # Loss to carry forward
    source_fy: int                # Original FY where loss occurred
```

**Gain.action audit trail**:
- `"loss"`: Sold at a loss (prioritized for harvesting)
- `"discount"`: Sold at profit after 365+ days (50% CGT discount)
- `"fifo"`: Standard FIFO when no loss/discount priority

**CGT Discount**: 50% of profit if held >365 days (long-term holding).

---

## property expenses

```python
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
    life_years: int               # Depreciation schedule
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
    occupancy_pct: Decimal        # 0.0-1.0 (validated in __post_init__)
    rents: list[Rent] = None
    waters: list[Water] = None
    councils: list[Council] = None
    stratas: list[Strata] = None
    capital_works: list[CapitalWorks] = None
    interests: list[Interest] = None
    
    # Computed properties
    @property
    def total_rental_income(self) -> Money:        # Sum of all rents
    
    @property
    def total_expenses(self) -> Money:             # Waters + councils + stratas only
    
    @property
    def deductible_expenses(self) -> Money:        # total_expenses * occupancy_pct
    
    @property
    def net_rental_income(self) -> Money:          # rental - deductible_expenses
```

**Occupancy allocation**: Only `occupancy_pct` of expenses deductible (if home office / shared rental).

---

## household optimization

```python
@dataclass(frozen=True)
class Individual:
    name: str
    fy: int
    income: Money                 # Employment/business income
    deductions: list[Money] = None
    gains: list[Gain] = None
    losses: list[Loss] = None
    
    @property
    def total_deductions(self) -> Money:           # Sum of deductions[]
    
    @property
    def total_gains(self) -> Money:                # Sum of gains[].taxable_gain
    
    @property
    def total_losses(self) -> Money:               # Sum of losses[].amount
    
    @property
    def taxable_income(self) -> Money:             # income + gains - deductions - losses

@dataclass(frozen=True)
class Allocation:
    yours: Individual
    janice: Individual
    your_tax: Money
    janice_tax: Money
    
    @property
    def total(self) -> Money:                      # your_tax + janice_tax
```

**Allocation strategy** (in household.py):
1. `allocate_deductions()`: Fill tax-free thresholds first, then route excess to lower-bracket person
2. `optimize_household()`: Route combined deductions to minimize household tax liability

---

## deduction & summary

```python
@dataclass(frozen=True)
class Deduction:
    category: str                 # "groceries", "utilities", etc.
    amount: Money
    rate: Decimal                 # Weight applied (0.0-1.0)
    rate_basis: str               # "percentage" or "fixed"
    fy: int

@dataclass(frozen=True)
class Summary:
    category: str
    credit_amount: Decimal        # For categorized txns
    debit_amount: Decimal         # For splits
```

---

## holdings & portfolio

```python
@dataclass(frozen=True)
class Holding:
    ticker: str                   # "ASX:BHP", "VAS"
    units: Decimal
    cost_basis: Money             # Total purchase cost
    current_price: Money          # Per-unit market price
    
    @property
    def current_value(self) -> Money:              # units * current_price
    
    @property
    def unrealized_gain(self) -> Money:            # current_value - cost_basis
```

---

## validation rules

All dataclasses enforce invariants in `__post_init__`:

- **Money**: Always paired with Currency
- **Transaction**: `personal_pct` must be 0.0-1.0
- **Property**: `occupancy_pct` must be 0.0-1.0
- **Individual**: List fields default to `[]` (mutable default prevention)

---

**Last Updated**: Oct 21, 2025
