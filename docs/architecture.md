# taxing architecture

## design principles

### core tenets
- **Pure functions**: Logic is side-effect-free, testable without I/O
- **Immutability**: Frozen dataclasses prevent accidental mutations
- **Separation of concerns**: `core/` (domain), `io/` (adapters), `pipeline/` (orchestration)
- **Type safety**: Decimal + Money prevent silent arithmetic bugs (USD vs AUD)
- **No globals**: Config passed as arguments (not `conf.py` globals)

### why not tax-og architecture
1. **Global state**: `conf.py` at import time → hard to test, compose, run in parallel
2. **I/O tangled with logic**: CSV read/write mixed with calculations
3. **Imperative scripts**: Sequential 1_ingest.py → 2_label.py → hard to reuse
4. **No type safety**: Strings everywhere, easy to mix currencies or forget categories
5. **Opaque rules**: Text files with no validation on load

## domain model

### Money (type-safe arithmetic)
```python
@dataclass(frozen=True)
class Money:
    amount: Decimal        # Precise, no float rounding
    currency: str          # "AUD", "USD", etc.
```

Prevents silent bugs like USD + AUD = wrong total. All arithmetic explicit.

### Transaction (immutable record)
```python
@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Money
    description: str
    source_bank: str       # "ANZ", "CBA", "Wise"
    source_person: str     # "tyson", "janice"
    category: set[str] | None      # {"groceries", "transport"} or None
    is_transfer: bool = False
```

Classification adds categories post-ingestion (immutable, no mutation).

### Trade (FIFO, loss harvesting, CGT)
```python
@dataclass(frozen=True)
class Trade:
    date: date
    code: str              # "ASX:BHP", "CRYPTO:BTC"
    action: str            # "buy" or "sell"
    units: Decimal
    price: Money           # Price per unit
    fee: Money
    source_person: str
```

Fully specified trade record. No implied data.

### Gain (result of trade matching)
```python
@dataclass(frozen=True)
class Gain:
    fy: int                # Financial year (1=July-June)
    raw_profit: Money      # Before CGT discount
    taxable_gain: Money    # After CGT discount (50% if held >365 days)
    action: str            # "loss", "discount", "fifo" (audit trail)
```

Immutable result. Action field tracks which priority rule fired.

## core functions

### classify (transactions → categories)
```python
def classify(description: str, rules: dict[str, list[str]]) -> set[str]:
    """Match transaction description against rule keywords.
    
    Pure function, no side effects.
    Case-insensitive substring matching.
    Returns empty set if no match (unlabeled transaction).
    """
```

Simple + auditable. No ML = defensible to ATO. Keywords case-insensitive + deduplicated on load.

### deduce (transactions + weights → deductions)
```python
def deduce(txns: list[Transaction], weights: dict[str, float]) -> dict[str, Money]:
    """Apply percentage weights to categorized transactions.
    
    Multi-category handling: If txn has {"groceries", "utilities"}, split weight proportionally.
    Aggregates by category.
    Pure function.
    """
```

Defensible: 60% groceries deduction = explicit percentage, traceable.

### process_trades (trades → gains)
```python
def process_trades(trades: list[Trade]) -> list[Gain]:
    """FIFO with prioritization: loss > discount > FIFO.
    
    Algorithm:
    1. Sort trades by (code, date)
    2. Group by ticker code, maintain FIFO buffer
    3. For each sell order:
       a. Prioritize loss positions (buy_price >= sell_price)
       b. Then prioritize 365+ day holdings (CGT discount eligible)
       c. Fall back to FIFO (first in, first out)
    4. Handle partial fills (sell less than lot size)
    5. Calculate profit, apply CGT discount, emit Gain
    
    Pure function, no mutations (uses dataclasses.replace for partial fills).
    """
```

Three-tier priority ensures tax-optimal sequencing within a single sell order.

**Partial fill handling**:
```python
# Full lot consumed
buff.remove(sell_lot)

# Partial lot: use dataclasses.replace() for immutability
updated_lot = replace(
    sell_lot,
    units=sell_lot.units - units_to_sell,
    fee=Money(sell_lot.fee.amount - partial_fee, AUD),
)
buff[idx] = updated_lot
```

No mutation → no accidental side effects → easier to reason about.

## I/O patterns

### CSV converters (bank-specific)
```python
# src/io/converters.py

def anz_converter(row: pd.Series) -> Transaction:
    """ANZ export CSV → Transaction."""
    
def cba_converter(row: pd.Series) -> Transaction:
    """CBA export CSV → Transaction."""
    
def beem_converter(row: pd.Series) -> Transaction:
    """Beem (BNPL) transactions."""
    # Handles directionality (outgoing vs incoming)
    
def wise_converter(row: pd.Series) -> Transaction:
    """Wise multi-currency transactions."""
    # Preserves original currency (not converted to AUD)
```

Each converter is a pure function. Composition in `ingest.py`.

### Persistence (uniform CSV I/O)
```python
# src/io/persist.py

def txns_to_csv(txns: list[Transaction], path: str | Path) -> None:
    """Write transactions to CSV."""
    # Serializes category set as comma-separated values
    
def txns_from_csv(path: str | Path) -> list[Transaction]:
    """Read transactions from CSV."""
    # Deserializes comma-separated categories back to set
    
def trades_to_csv(trades: list[Trade], path: str | Path) -> None:
    """Write trades to CSV."""
    # Preserves Decimal precision (not float)
    
def trades_from_csv(path: str | Path) -> list[Trade]:
    """Read trades from CSV."""
    
def gains_to_csv(gains: list[Gain], path: str | Path) -> None:
    """Write gains to CSV."""
    
def gains_from_csv(path: str | Path) -> list[Gain]:
    """Read gains from CSV."""
```

**Pattern note** (for Phase 2b): All follow identical structure. Future: Generic codec with dataclass field metadata.

### Ingestion (CSV → domain)
```python
# src/io/ingest.py

def ingest_dir(base_dir: str | Path) -> list[Transaction]:
    """Load all transactions from directory.
    
    Structure: {base_dir}/{person}/raw/{bank}.csv
    Auto-detects persons, banks.
    """
    
def ingest_trades(path: str | Path, person: str) -> list[Trade]:
    """Load trades from single CSV file."""
    
def ingest_trades_dir(base_dir: str | Path, persons: list[str] | None = None) -> list[Trade]:
    """Load all trades from directory.
    
    Structure: {base_dir}/{person}/raw/equity.csv
    Sorts by (code, date) for FIFO processing.
    """
```

## pipeline orchestration

### main flow
```python
# src/pipeline.py

def run(base_dir: str | Path, fiscal_year: str) -> dict[str, dict[str, object]]:
    """
    Ingest → Classify → Deduce → Trades → Persist
    
    1. ingest_dir(): Load all txns from {fy}/raw/
    2. ingest_trades_dir(): Load all trades from {fy}/
    3. load_rules(): Load classification rules
    4. weights_from_csv(): Load deduction weights
    
    For each person:
       5. Filter txns by source_person
       6. classify() each txn
       7. deduce() weighted deductions
       8. summarize() by category
       9. process_trades() for capital gains
       10. Persist: transactions.csv, deductions.csv, summary.csv, gains.csv
    
    Returns: {person → {txn_count, classified_count, deductions, gains_count}}
    """
```

**Single ingest pass** (all people), then per-person processing → efficient.

### data flow diagram
```
{fy}/raw/{person}/{bank}.csv         ← Bank CSVs
{fy}/{person}/raw/equity.csv         ← Trade CSVs
rules/*.txt                          ← Classification rules
weights.csv                          ← Deduction percentages
        ↓
  ingest_dir() + ingest_trades_dir()
        ↓
  All txns + trades (unified)
        ↓
  For each person:
    classify() + deduce()            ← Core domain logic
    process_trades()                 ← FIFO + loss harvesting
        ↓
  {fy}/{person}/data/{transactions,deductions,summary,gains}.csv
```

## testing strategy

### unit tests (tests/unit/core/)
- Pure logic, no I/O
- Mock all dependencies
- Test contracts, not implementation
- Aim for 100% coverage (pure functions, no excuses)

Example:
```python
def test_process_trades_loss_harvesting():
    """Loss positions prioritized over FIFO."""
    trades = [
        Trade(date=2023-01-01, code="ASX:BHP", action="buy", units=100, price=10, fee=5),
        Trade(date=2023-06-01, code="ASX:BHP", action="buy", units=100, price=15, fee=5),
        Trade(date=2023-12-01, code="ASX:BHP", action="sell", units=100, price=12, fee=5),
    ]
    gains = process_trades(trades)
    
    # Should sell the 15 AUD lot (loss) first
    assert gains[0].action == "loss"
    assert gains[0].raw_profit.amount == Decimal(-300)
```

### integration tests (tests/integration/)
- Full pipeline + real CSV I/O
- Validate end-to-end correctness
- Example: Parity vs tax-og (test_trades_parity.py)

```python
def test_parity_with_tax_og(tax_og_equity_file):
    """Verify against real tax-og data."""
    trades = ingest_trades(tax_og_equity_file, "tyson")
    gains = process_trades(trades)
    
    # Basic invariants
    assert len(gains) > 0
    assert all(g.fy > 0 for g in gains)
    assert all(g.action in ["loss", "discount", "fifo"] for g in gains)
```

## known limitations

### Phase 1 (transaction pipeline)
1. **International transactions**: Dropped (lost deductions)
2. **High percentages** (>60%): May trigger ATO attention
3. **Duplicate detection**: Weak, can amplify deductions
4. **Transfer detection**: Incomplete (P2P transfers not excluded)

### Phase 2a (capital gains)
1. **Bracket-unaware**: No consideration of tax bracket headroom (Phase 2b)
2. **No multi-year planning**: Can't defer gains to better bracket year
3. **No loss carryforward**: Can't track unused losses from prior years
4. **Crypto not tested**: Placeholder (need test fixtures)

### Future (Phase 2b+)
- Medicare Levy cliff handling
- HELP repayment thresholds
- Integer Linear Programming optimization (scipy)

---

**Last Updated**: Oct 21, 2025
