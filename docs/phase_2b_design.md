# Phase 2b: Bracket-Aware Capital Gains Sequencing

**Note**: Phase 2a (FIFO + loss harvesting + CGT discount) is complete and integrated into pipeline.

**Goal**: Phase 2b adds bracket awareness for optimal tax efficiency across income levels.

Build bracket-aware capital gains sequencing that maximizes tax efficiency across multiple trading platforms (equities, crypto, forex) using constraint optimization.

---

## Problem Statement

**Current approach (tax-og)**: Naive FIFO with heuristics
- Sequential lot matching: loss > discount > FIFO
- No awareness of tax brackets or other income
- Suboptimal for varying income years (unemployed = different strategy)

**Better approach**: Bracket-aware sequencing
- Know your total taxable income for the FY
- Calculate remaining headroom at each tax bracket
- Sequence gain realization to fill brackets optimally
- Defer high-gain years if better bracket available

**Example**:
```
FY25 income: $0 (unemployed)
Tax-free threshold: $18,200
Available gains:
  - Position A: $15,000 profit (held 2yr, 50% discount = $7,500 gain)
  - Position B: $5,000 profit (held 6mo, no discount = $5,000 gain)
  
Optimal: Realize both → $12,500 gains (0% tax, under threshold)
Naive FIFO: Might sell high-gain positions first → trigger higher bracket
```

---

## Architecture Overview

### Trade Domain Model (New)

```python
# src/core/models.py (extend)

@dataclass(frozen=True)
class Trade:
    """Individual equity/crypto trade record."""
    date: date
    code: str                      # ticker: "ASX:BHP", "CRYPTO:BTC", "FOREX:EURUSD"
    action: Literal["buy", "sell"]
    units: Decimal                 # quantity of shares/coins
    price_per_unit: Money          # price at time of trade
    fee: Money
    source: str                    # platform: "Commsec", "Crypto.com", "Kraken"
    source_person: str             # who owns the trade

@dataclass(frozen=True)
class CapitalGainResult:
    """Per-FY capital gains result."""
    fy: int
    raw_profit: Money              # profit before any discount
    taxable_gain: Money            # profit after CGT discount (Australia: 50%)
    realized_sequence: list[str]   # which positions sold and in what order (audit trail)
    optimization_score: float      # 0-1, how well we filled brackets

@dataclass(frozen=True)
class TaxBracket:
    """Australian tax bracket."""
    lower_bound: int               # e.g., 0
    upper_bound: int               # e.g., 18200
    marginal_rate: float           # e.g., 0.0
    medicare_levy: bool            # applies to this bracket?
    
@dataclass(frozen=True)
class TaxYear:
    """Complete tax picture for one FY."""
    fy: int                        # 2025
    income_from_employment: Money  # salary, wages
    income_from_other: Money       # rental, interest, etc.
    tax_brackets: list[TaxBracket]
    capital_losses_carried_forward: Money  # unused losses from prior years
```

### Trade Converters (New)

```python
# src/io/trade_converters.py (new)

def commsec_converter(row: pd.Series) -> Trade:
    """ASX trades from Commsec CSV export."""
    pass

def crypto_com_converter(row: pd.Series) -> Trade:
    """Crypto.com trades."""
    pass

def kraken_converter(row: pd.Series) -> Trade:
    """Kraken cryptocurrency trades."""
    pass

def interactive_brokers_converter(row: pd.Series) -> Trade:
    """IB account statements."""
    pass
```

### Capital Gains Core Logic (New)

```python
# src/core/capital_gains.py (new)

def load_trades(base_dir: Path, fy: str, person: str) -> list[Trade]:
    """Load all trades for a person across all platforms."""
    pass

def is_cgt_discount_eligible(buy_date: date, sell_date: date) -> bool:
    """Australian CGT discount: 50% if held >12 months."""
    return (sell_date - buy_date).days > 365

def calculate_raw_profit(trade_buy: Trade, trade_sell: Trade, units: Decimal) -> Money:
    """Profit = units * (sell_price - buy_price) - fees."""
    pass

def calculate_taxable_gain(profit: Money, is_discounted: bool) -> Money:
    """Apply CGT discount if eligible."""
    if is_discounted:
        return profit * 0.5
    return profit

def bracket_aware_sequencing(
    trades: list[Trade],
    tax_year: TaxYear
) -> dict[int, CapitalGainResult]:
    """Optimize which positions to sell in which order.
    
    Returns capital gains by FY with optimization details.
    """
    # 1. Group trades by code (ticker)
    # 2. For each code, build FIFO buffer
    # 3. For each sell, score available lots:
    #    - Is it at a loss? (harvest early)
    #    - Is it eligible for discount? (defer if better bracket next year)
    #    - Current tax bracket headroom?
    # 4. Greedily fill brackets: sell to maximize tax efficiency
    # 5. Return sequence + efficiency score
    pass

def bracket_headroom(tax_year: TaxYear) -> dict[int, int]:
    """Calculate available income at each bracket.
    
    Returns: {bracket_upper_bound: remaining_headroom}
    """
    current_taxable = (
        tax_year.income_from_employment +
        tax_year.income_from_other
    )
    headroom = {}
    for bracket in tax_year.tax_brackets:
        if current_taxable < bracket.upper_bound:
            headroom[bracket.upper_bound] = bracket.upper_bound - current_taxable.amount
        current_taxable += current_taxable  # Track cumulative
    return headroom

def optimize_sequence(
    available_gains: list[tuple[Trade, Trade, Decimal, Money]],  # (buy, sell, units, profit)
    tax_year: TaxYear
) -> list[tuple[Trade, Trade, Decimal, Money, str]]:
    """Reorder which positions to realize first.
    
    Strategy:
    1. Prioritize loss harvesting (realize losses to offset gains)
    2. Fill tax-free threshold with discounted gains
    3. Fill lower brackets with non-discounted gains
    4. Defer high-gain, high-bracket positions to next year
    
    Returns: Ordered list of (buy, sell, units, profit, action_reason)
    """
    pass
```

### Constraint Optimization (Optional Phase 2b)

For more complex scenarios (multi-year optimization, Medicare Levy cliffs, HELP repayment):

```python
# src/core/optimization.py (optional)

def integer_linear_programming_optimize(
    available_gains: list[GainOption],
    tax_brackets: list[TaxBracket],
    constraints: dict
) -> SolutionResult:
    """Use scipy.optimize or pulp to find global optimum.
    
    This is overkill for most cases but handles edge cases:
    - Maximize total income while minimizing tax
    - Handle Medicare Levy thresholds
    - Multi-year planning (realize in FY25 vs FY26)
    """
    pass
```

---

## Data Flow: Trade to Optimized Gains

```
Equity platforms (CSV exports):
  - Commsec: ASX trades
  - Crypto.com: Crypto trades
  - Kraken: Crypto trades
  - Interactive Brokers: Global equities
        ↓
  [Trade Converters]
        ↓
  Unified Trade list (all platforms)
        ↓
  [Bracket-Aware Sequencing]
        ↓
  Capital gains by FY (optimized)
        ↓
  gains.csv + optimization_report.md
```

---

## Tax Law Context (Australia)

### CGT Discount
- Individual taxpayers: 50% discount if held >12 months
- Calculation: Include only 50% of gain in assessable income
- Example: $1000 gain (held 2yr) → $500 taxable

### Tax Brackets FY2024-25
```
$0-$18,200: $0 (tax-free threshold)
$18,201-$45,000: 19%
$45,001-$120,000: 32.5%
$120,001-$180,000: 37%
$180,001+: 45%
Medicare Levy: 2% (mostly, exceptions exist)
```

### Loss Harvesting
- Capital losses can offset capital gains
- Unused losses carry forward indefinitely
- Cannot offset other income (only capital gains)

### HELP Repayment
- If income > $54,435, you may owe HELP repayment
- Rate scales with income
- Relevant for FY sequencing

---

## Implementation Status

### Phase 2a: FIFO + Loss Harvesting + CGT Discount ✅ COMPLETE
- [x] Trade domain model (Trade, Gain dataclasses)
- [x] FIFO buffer + loss harvesting + CGT discount (50% for >365 days)
- [x] Trade I/O converters (trades_to_csv, trades_from_csv, gains_to_csv, gains_from_csv)
- [x] Trade ingestion (ingest_trades, ingest_trades_dir)
- [x] Pipeline integration (trades stage after deduce)
- [x] Unit tests (7 tests: calc_fy, cgt_discount, FIFO, loss harvesting, partial fills)
- [x] Integration tests (parity vs tax-og real data, CSV roundtrip)
- [x] 79 tests passing, zero lint

### Phase 2b: Bracket-Aware Sequencing (Next Priority)
- [ ] Tax year model (TaxBracket, TaxYear)
- [ ] Bracket headroom calculation
- [ ] Greedy sequencing algorithm (fill brackets optimally)
- [ ] Trade converters (Commsec, Crypto.com, Kraken as data fixtures)
- [ ] Tests: unit tests for bracket logic, integration test for bracket-optimal sequencing
- [ ] CLI: `taxing gains --fy fy25 --person tyson --income-from-employment 80000`

### Phase 2c: Multi-Year Planning (Optional)
- [ ] Defer gains to next FY if better bracket
- [ ] Track tax losses carried forward
- [ ] Estimate next FY bracket (if income projections available)

### Phase 2d: Advanced Constraints (Nice-to-Have)
- [ ] Medicare Levy cliff handling
- [ ] HELP repayment threshold
- [ ] ILP optimization (scipy.optimize)

---

## Test Strategy

### Unit Tests
```python
# tests/unit/core/test_capital_gains.py

def test_cgt_discount_eligible_held_over_365_days():
    """Positions held >365 days get 50% discount."""
    pass

def test_bracket_headroom_unemployed():
    """If income=$0, all $18,200 tax-free threshold available."""
    pass

def test_bracket_headroom_high_income():
    """If income=$150k, zero headroom at first bracket."""
    pass

def test_loss_harvesting_prioritized():
    """Loss positions sell before profitable ones."""
    pass

def test_sequencing_fills_tax_free_first():
    """Gains sequence to fill $18,200 threshold first."""
    pass

def test_optimization_score_perfect():
    """If gains exactly fit brackets, score = 1.0."""
    pass

def test_optimization_score_wasteful():
    """If gains overflow brackets unnecessarily, score < 1.0."""
    pass
```

### Integration Tests
```python
# tests/integration/test_gains_pipeline.py

def test_end_to_end_single_ticker_fifo():
    """Buy low, sell high, FIFO matching."""
    pass

def test_end_to_end_multi_ticker_loss_harvesting():
    """Multiple tickers, loss in one, gain in another."""
    pass

def test_end_to_end_cgt_discount():
    """Position held >12mo gets 50% discount."""
    pass

def test_end_to_end_bracket_optimization():
    """Sequences gains to maximize tax efficiency."""
    pass
```

---

## CLI Interface (Phase 2a)

```bash
# Calculate capital gains for a FY
taxing gains --fy fy25 --person tyson --income-from-employment 80000

# Output: gains.csv + summary
fy,taxable_gain,raw_profit,efficiency,positions
25,12500,25000,0.92,BHP:100,BTC:2.5

# Optional: Show detailed sequence
taxing gains --fy fy25 --person tyson --income-from-employment 80000 --verbose

# Optional: Defer gains to next FY if better bracket
taxing gains --fy fy25 --person tyson --income-from-employment 80000 --project-fy26 100000
```

---

## References

### Australian Tax Office
- CGT Discount: https://www.ato.gov.au/individuals/capital-gains-tax/
- Capital Losses: https://www.ato.gov.au/individuals/capital-gains-tax/working-out-your-capital-gains-tax/
- Tax Brackets: https://www.ato.gov.au/Individuals/Income-and-deductions/Tax-rates/

### Code References
- `tax-og/src/pipeline/6_gains.py`: Current FIFO + heuristics (port core logic)
- `taxing/src/core/models.py`: Extend with Trade, CapitalGainResult
- `taxing/src/core/deduce.py`: Similar pattern to capital_gains.py

---

## Continuation Notes

For next session (Phase 2b):
1. Start here: Read `docs/context.md` (1 min)
2. Read `docs/architecture.md` (5 min)
3. Read this file (5 min)
4. Current state: Phase 2a complete (79 tests, capital gains core)
5. Next work: Implement Phase 2b (bracket-aware sequencing)
6. Data needed: Sample trade CSVs from Commsec, Crypto.com, Kraken (test fixtures)

### Command
```bash
just test  # Verify all 79 tests still passing
```

---

**Last Updated**: Oct 21, 2025
**Model**: claude-haiku-4-5
**Status**: Phase 2a complete, Phase 2b ready for design review
