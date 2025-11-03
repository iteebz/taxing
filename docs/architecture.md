# taxing architecture

## design principles

### core tenets
- **Pure functions**: Logic is side-effect-free, testable without I/O
- **Immutability**: Frozen dataclasses prevent accidental mutations
- **Unified data model**: Single transaction/deduction/gains CSVs (all people, all years)
- **Deterministic pipeline**: Raw input → classify → deduce → persist (no intermediate state)
- **Type safety**: Decimal for monetary precision
- **No globals**: Config passed as arguments

## domain model

### Monetary Amounts (Decimal for precision)
All monetary amounts are represented using Python's `Decimal` type for precise calculations, avoiding floating-point inaccuracies.

### Transaction (immutable record)
```python
@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Decimal
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
    price: Decimal           # Price per unit
    fee: Decimal
    source_person: str
```

Fully specified trade record. No implied data.

### Gain (result of trade matching)
```python
@dataclass(frozen=True)
class Gain:
    fy: int                # Financial year (1=July-June)
    raw_profit: Decimal      # Before CGT discount
    taxable_gain: Decimal    # After CGT discount (50% if held >365 days)
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

### deduce (transactions + ATO rates → deductions)
```python
def deduce(txns: list[Transaction], weights: dict, fy: int, conservative: bool) -> list[Deduction]:
    """Calculate deductions based on ATO rates and transaction details.
    
    Pure function, no side effects.
    Applies ATO-published rates, personal_pct, and handles conservative mode.
    Returns a list of Deduction objects.
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
    fee=sell_lot.fee - partial_fee,
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

def ingest_year(base_dir: str | Path, year: int, persons: list[str] | None = None) -> list[Transaction]:
    """Load transactions for a fiscal year.
    
    Structure: {base_dir}/data/raw/fy{year}/{person}/*.csv
    """

def ingest_all_years(base_dir: str | Path, persons: list[str] | None = None) -> list[Transaction]:
    """Load all transactions across all fiscal years.
    
    Structure: {base_dir}/data/raw/fy*/{person}/*.csv
    Returns deduplicated, chronologically sorted transactions.
    """
```

### Path helpers
```python
# src/lib/paths.py - Centralized path resolution

data_root(base_dir) → Path           # data/
data_raw(base_dir) → Path            # data/raw/
data_raw_fy(base_dir, fy) → Path     # data/raw/fy{fy}/
transactions_csv(base_dir) → Path    # data/transactions.csv
deductions_csv(base_dir) → Path      # data/deductions.csv
gains_csv(base_dir) → Path           # data/gains.csv
```

## pipeline orchestration

### main flow
```python
# src/pipeline.py

def run(base_dir: str | Path, persons: list[str] | None = None) -> dict[str, dict[str, object]]:
    """
    Universe-wide pipeline: Ingest → Classify → Deduce → Trades → Persist
    
    1. ingest_all_years(): Load all txns from data/raw/fy*/{person}/*.csv
    2. ingest_all_trades(): Load all trades
    3. dedupe(): Remove duplicates
    4. classify(): Universe-wide classification (all txns against rules)
    5. For each person:
       - Filter txns by individual
       - deduce(): ATO-based deductions
       - process_trades(): FIFO + loss harvesting
    6. to_csv(): Persist unified CSVs: data/transactions.csv, data/deductions.csv, data/gains.csv
    
    Returns: {person → {txn_count, classified_count, deductions, gains_count}}
    """
```

**Key design**: Single ingest + classification pass (universe-wide), then per-person deduction/trade processing. Output is unified CSVs (all people, all years in one file).

### data flow diagram
```
data/raw/fy*/{person}/*.csv          ← Raw bank CSVs (inputs)
rules/*.txt                          ← Classification keywords
        ↓
  ingest_all_years() + ingest_all_trades()
        ↓
  All txns + trades (deduplicated)
        ↓
  classify(): Universe-wide (single pass)
        ↓
  For each person:
    deduce() + process_trades()      ← Per-person calculations
        ↓
  data/transactions.csv              ← All people, all years, classified
  data/deductions.csv                ← All people, all years, by category & fy
  data/gains.csv                     ← All trades, all people, capital gains
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
    # Note: The 'action' field is part of CapitalGainResult, not the core Gain object.
    assert gains[0].raw_profit == Decimal(-300)
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

**Last Updated**: Nov 4, 2025
**Architecture**: Unified data model (all people, all years in single CSV tables)
