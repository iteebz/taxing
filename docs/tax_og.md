# Tax-OG Porting Analysis: 6_gains.py, 7_property.py, 5_wrap.py → Taxing

## Executive Summary

Tax-og contains three specialized modules for specific tax computations beyond the core classification pipeline. These modules represent distinct business domains that can be modularized cleanly into the taxing architecture. Each requires a different integration strategy based on its input/output characteristics and algorithmic complexity.

---

## Comprehensive Comparison Table

| Aspect | 6_gains.py (FIFO Capital Gains) | 7_property.py (Property Expenses) | 5_wrap.py (Year Summary Report) |
|--------|----------------------------------|-----------------------------------|--------------------------------|
| **WHAT IT DOES** | | | |
| Core business logic | FIFO buy/sell matching for equities; CGT discount (50% gains if >12mo hold); loss harvesting optimization; capital gains tax calculation across FY boundaries | Aggregates property investment expenses from separate CSV files; calculates total rent, water, council rates, strata fees; produces expense breakdown | Generates Spotify-style annual financial summary; categorizes spending (discretionary vs non-discretionary); identifies income, investments, obfuscated transactions; calculates average spend/metrics |
| Algorithm summary | 1. Load equity trades (buy/sell); 2. FIFO buffer per code; 3. On sell: prefer loss-making lots, then 12mo+ holdings for 50% discount, else FIFO; 4. Accrue gains with discount applied; 5. Calculate efficiency% (actual vs best-case discount) | 1. Load 4 CSV files (rent, water, council, strata); 2. Sum each category; 3. Print totals | 1. Filter transactions by category; 2. Calculate spending by category/subcategory; 3. Compute percentages of income; 4. Format for human readability; 5. Flag outliers (electronics, beems, obfuscated) |
| Maturity | Production-ready, extensively tested via comments (full/partial/overflow scenarios for each action) | MVP, minimal logic (pure aggregation) | Production-ready, handles edge cases (zero income, transfers, multi-category txns) |
| **DATA SOURCES** | | | |
| Input files | `equity/{name}.csv` with columns: date, code, action (buy/sell), units, price, fee, amount | `archive/{fy}/{name}/property/` with 4 CSVs: rent.csv, water.csv, council.csv, strata.csv (columns: amount) | `{combined_labeled_path}` CSV with columns: category, amount, is_transfer, description |
| Input format | CSV: per-trade rows (buy/sell history) | CSV: separate files per expense type (flat lists of amounts) | CSV: categorized transactions (output from pipeline) |
| Data contract | Validates amount = ±(units × price) - fee for each trade; flags mismatches >$0.01 | No validation (trusts CSV format) | Expects category field to be populated, is_transfer flag present |
| Sample data | Trades: SYI (Aussie Dividends ETF), NDQ (Tech), ETHI (Sustainability), SVU (Spaceship) | Hypothetical example: 4 CSV files per property | Transactions with categories: income, investment, eating_out, food_delivery, etc. |
| External deps | None (pure pandas) | None (pure pandas) | Depends on pipeline output (classify stage must complete first) |
| **DATA OUTPUTS** | | | |
| Output format | Console printout (human-readable text) + implicit data structures (gains_by_fy dict) | Console printout (4 lines, one per category) | Console printout (multi-section report with statistics) |
| Metrics produced | Per-code position; per-FY: {profits, capital_gains, discount_efficiency%} | Per-category totals: rent, water, council, strata | Per-category spend; income; investment status; food metrics (avg cost/meal); discretionary breakdown; obfuscated txn summary |
| Exportability | Not exportable (printouts only); gains_by_fy/profits_by_fy are local vars | Not exportable (printouts only) | Not exportable (printouts only) |
| Audit trail | Prints every trade + sell decision (loss/discount/FIFO) with reasoning | None (single sum operation) | None (aggregation only) |
| **CORE ALGORITHMS** | | | |
| Algorithm 1 | **FIFO Buffer Matching**: Per equity code, maintain list of buy trades; on sell, prioritize by: (a) loss-making (price > sell price), (b) 12mo+ old (for CGT discount), (c) FIFO order | **Simple Summation**: `total = sum(df[column])` for each file | **Category Aggregation**: Filter txns by category + non-transfers; sum amounts (negative=outbound spending) |
| Algorithm 2 | **Partial Fill**: If units_to_sell < holdings of a lot, split the lot; allocate fee pro-rata by units | **N/A** | **Percentage Composition**: For each subcategory, compute `spend / total_spend` |
| Algorithm 3 | **CGT Discount Logic**: If hold >365 days, gain = profit/2; else gain = profit (no discount); accrue into FY-keyed dict | **N/A** | **Income Normalization**: `pct_of_income(spend) = spend / income * 100` (handles zero income case) |
| Algorithm 4 | **Efficiency Calculation**: `(actual_gain - best_case) / (profit - best_case)` measures how well loss/discount harvesting worked | **N/A** | **Outlier Detection**: Search description for "beem it" (obfuscated P2P); flag electronics category |
| Time complexity | O(n·m) where n = trades, m = avg holdings per code (typically small); sell operation is O(m) | O(n) where n = sum of rows across 4 files | O(n) where n = total txns |
| Space complexity | O(c·h) where c = codes, h = avg holdings per code | O(1) (only aggregates) | O(c) where c = categories |
| **TESTABILITY** | | | |
| Unit test surface | `validate()` (amount check), FIFO logic (append), sell logic (prefer loss/discount), partial fill, discount application, efficiency calc | `sum()` operations (no extraction needed) | Category filtering, pct calc, outlier detection |
| Test scenarios (buy/sell) | • Regular buy (append to buffer); • Full sell (remove from buffer, FIFO); • Partial sell (split lot, pro-rata fee); • Overflow sell (multiple buffer items); • Loss-making lot sale; • 12mo+ discount lot sale; • Mixed strategies in single sell; • Multi-sell (exhaust buffer) | • Empty file (zero sum); • Single category; • Multiple categories; • Zero amounts | • Zero income (edge case); • No transactions; • All transfers (filtered out); • Multi-category txn; • Missing category (None) |
| Mocking strategy | Mock `pd.read_csv()` to return DataFrame with known trades; validate buffer state after each operation | Mock `pd.read_csv()` × 4; validate total equals sum of inputs | Mock pipeline output CSV; validate spend calculations against manual totals |
| Assertion examples | `assert buffer_before == 2; assert buffer_after == 1; assert gain == expected_gain; assert efficiency == expected%` | `assert sum(rent, water, council, strata) == expected_total` | `assert pct_of_income(spend) == (spend / income); assert len(beems) > 0 implies warning printed` |
| Regression risk | High (complex FIFO logic + discount rules; easy to break on edge cases) | Low (pure aggregation) | Medium (multiple aggregations + branching logic) |
| **PORTING STRATEGY** | | | |
| Port as | Pure function module: `gains.CapitalGains` (dataclass-based) | Pure function module: `property.PropertyExpenses` | Pure function module (or report generator): `wrap.AnnualSummary` |
| Input transformation | `pd.DataFrame → list[Trade]` dataclass; validate; group by code | CSV path list → `list[PropertyExpense]` dataclass | Use existing `list[Transaction]` + `dict[str, float]` weights |
| Core logic extraction | Extract FIFO + discount logic into pure functions: `fifo_match(trades) → list[MatchResult]`, `apply_discount(result) → CapitalGain`; remove pandas dependency | Extract sum logic into pure function: `aggregate_expenses(expenses) → dict[str, Money]` | Extract calculation logic into pure functions: `calc_category_spend(txns, cat) → Money`, `calc_income_pct(spend, income) → str` |
| Output contract | Return dataclass: `CapitalGainsSummary(gains_by_fy: dict[int, Money], trades_matched: list[MatchResult], efficiency: float)` | Return dataclass: `PropertyExpensesSummary(rent: Money, water: Money, council: Money, strata: Money, total: Money)` | Return dataclass: `AnnualSummary(income: Money, spend_by_cat: dict[str, Money], discretionary: Money, non_discretionary: Money, outliers: list[str])` |
| Error handling | • Invalid CSV format → ValueError; • Incomplete trades (units/price missing) → ValueError; • Negative units → ValueError; • Date parsing → use pipeline's date logic | • Missing file → FileNotFoundError or graceful (zero); • Invalid amounts (non-numeric) → ValueError | • No transactions → return defaults; • Zero income → set pct to "N/A"; • Missing category → skip txn |
| File location | `src/core/gains.py` (pure logic); tests in `tests/unit/core/test_gains.py` | `src/core/property.py` (pure logic); tests in `tests/unit/core/test_property.py` | `src/core/wrap.py` (pure logic); optional `src/io/reports.py` for console output formatting |
| Pipeline integration | 1. Run classify + deduce (existing); 2. Load equity trades separately; 3. Call `gains.calculate(trades, fy) → CapitalGainsSummary`; 4. Append to pipeline results | 1. Load property expense CSVs (new I/O adapter in `src/io/property.py`); 2. Call `property.aggregate(expenses) → PropertyExpensesSummary`; 3. Append to pipeline results | 1. Run classify + deduce (existing); 2. Call `wrap.generate_summary(txns, weights, fy) → AnnualSummary`; 3. Format for console or export |
| CLI integration | `taxing gains --fy fy25 --person tyson --equity-file equity/tyson.csv` | `taxing property --fy fy25 --person tyson --base-dir archive/` | `taxing wrap --fy fy25 --person tyson` |
| Tests per module | ~15 tests (FIFO variants, discount logic, efficiency calc, edge cases) | ~8 tests (aggregation, missing files, zero amounts) | ~12 tests (category filtering, pct calc, income normalization, outlier detection) |
| **ARCHITECTURAL PATTERNS** | | | |
| Pattern 1 | **Immutable Trade/Match Result**: `@dataclass(frozen=True) class Trade(...)` and `MatchResult(...)` to prevent accidental mutations | **Immutable Expense**: `@dataclass(frozen=True) class PropertyExpense(...)` | **Immutable summary result**: `@dataclass(frozen=True) class AnnualSummary(...)` |
| Pattern 2 | **Pure functions**: `fifo_match(trades) → list[MatchResult]` has no side effects; testable in isolation | **Pure aggregation**: Single function with clear I/O contract | **Pure calculation**: `calc_category_spend()`, `calc_income_pct()` are pure; console formatting is separate |
| Pattern 3 | **No global state**: Config (FY, person, name) passed as args; no `conf.py` dependency | **No global state**: File paths passed as args | **No global state**: Txns + weights passed as args (no dependency on pipeline's internal state) |
| Pattern 4 | **Validated input**: Validate CSV format on load (amount = ±units×price - fee); fail early with clear error | **Graceful degradation**: Missing file → zero amount (rather than crash); trusts data format | **Defensive filtering**: Handle None categories, missing transfers flag, zero income gracefully |
| Pattern 5 | **Testable reporting**: Separate logic (pure calcs) from presentation (console formatting); can test logic + mock formatting | **Minimal presentation logic**: Pure calculation is 10 lines; no mocking needed | **Modular report sections**: Each section (income, food, discretionary) is independently calculable |
| Separation of concerns | **Domain** (gains calc) ≠ **I/O** (CSV load) ≠ **Presentation** (console print); each is testable | **Domain** (expense sum) ≠ **I/O** (CSV load); domain has ~2 lines of logic | **Domain** (summary calc) ≠ **I/O** (CSV load from pipeline); presentation (console print) is generated from domain result |
| Reusability | High: `calculate(trades, fy)` can be called from CLI, pipeline, or interactive session; no CSV coupling | High: `aggregate(expenses)` can accept any expense list, not tied to file format | High: `generate_summary(txns, weights, fy)` is pure; can be called from CLI, web API, or batch | 
| **PORTING EFFORT** | | | |
| Refactor LOC | 6_gains.py: ~150 LOC → 80 LOC (remove pandas loops, extract pure functions) | 7_property.py: ~30 LOC → 15 LOC (direct function call) | 5_wrap.py: ~125 LOC → 60 LOC (extract calcs, inline presentation) |
| New tests LOC | +150 tests (comprehensive FIFO + discount scenarios) | +80 tests (happy path + edge cases) | +100 tests (category filtering, pct calc, outliers) |
| New I/O adapters | `src/io/equity.py` (load equity trades from CSV, validate) | `src/io/property.py` (load property CSVs, return list[PropertyExpense]) | None (use existing pipeline output) |
| Risk level | Medium-High (complex logic, easy to introduce bugs in FIFO/discount; needs thorough testing) | Low (trivial logic) | Medium (multi-step aggregations, edge cases in filtering) |
| Breaking changes | None (pure additions; wrap.py + property.py become optional modules, gains.py is new) | None | None |
| Backward compatibility | Tax-og scripts will continue to work; taxing gains module is new functionality | Tax-og scripts will continue to work; property module is new to taxing | Tax-og scripts will continue to work; wrap module is optional report generator in taxing |

---

## Porting Roadmap

### Phase 1: Property (Lowest Risk, Highest Value/Effort Ratio)
1. Create `src/io/property.py` → load rent/water/council/strata CSVs
2. Create `src/core/property.py` → `aggregate_expenses(list[PropertyExpense]) → PropertyExpensesSummary`
3. Write tests (5-8 cases: happy path, missing files, zero amounts)
4. Integrate into pipeline: optional property expense calculation
5. **Effort**: 2-3 hours | **Risk**: Low

### Phase 2: Wrap (Medium Risk, High Clarity)
1. Extract 5_wrap.py logic into pure functions in `src/core/wrap.py`
2. Create `AnnualSummary` dataclass (return type)
3. Write tests (8-10 cases: income calc, category spend, pct normalization, outlier detection)
4. Create `src/io/reports.py` for console formatting (separate presentation from logic)
5. Integrate into pipeline: optional wrap report generation
6. **Effort**: 4-5 hours | **Risk**: Medium

### Phase 3: Gains (Highest Risk, Highest Complexity)
1. Create `src/io/equity.py` → load equity trades, validate
2. Create `src/core/gains.py` → `calculate_capital_gains(trades, fy) → CapitalGainsSummary`
3. Extract FIFO logic into testable functions:
   - `fifo_buffer(trades) → list[MatchResult]` (per code)
   - `apply_discount(match_result, hold_days) → CapitalGain`
   - `calculate_efficiency(gains, profits) → float`
4. Write comprehensive tests (15-20 cases: all FIFO scenarios, discount variants, edge cases)
5. Integrate into pipeline: optional capital gains calculation
6. **Effort**: 6-8 hours | **Risk**: Medium-High

---

## Data Flow (After Porting)

```
PHASE 1: Classification Pipeline (Existing)
────────────────────────────────────────────
raw/{fy}/{person}/*.csv
    → ingest() → list[Transaction]
    → classify() → set[str] categories per txn
    → deduce() → dict[str, Money] deductions
    → persist() → data/{person}/deductions.csv

PHASE 2: Optional Supplementary Modules
───────────────────────────────────────────
A. Capital Gains (New)
   equity/{person}.csv → io.equity.load_trades() → list[Trade]
                      → core.gains.calculate() → CapitalGainsSummary
                      → results.gains_by_fy dict

B. Property Expenses (New)
   archive/{fy}/{person}/property/*.csv → io.property.load_expenses() → list[PropertyExpense]
                                       → core.property.aggregate() → PropertyExpensesSummary
                                       → results.property_totals dict

C. Annual Wrap Report (New)
   data/{person}/transactions.csv (pipeline output)
                                   → core.wrap.generate_summary() → AnnualSummary
                                   → console report or JSON export
```

---

## Key Integration Points with Existing Taxing Architecture

### 1. Models (Extend `src/core/models.py`)

```python
@dataclass(frozen=True)
class Trade:
    date: date
    code: str
    action: str  # "buy" | "sell"
    units: Decimal
    price: Decimal
    fee: Decimal
    amount: Money

@dataclass(frozen=True)
class PropertyExpense:
    type: str  # "rent" | "water" | "council" | "strata"
    amount: Money

@dataclass(frozen=True)
class CapitalGain:
    trade: Trade
    profit: Money
    gain: Money  # profit with discount applied
    discount_applied: bool
    hold_days: int

@dataclass(frozen=True)
class AnnualSummary:
    income: Money
    spend_by_category: dict[str, Money]
    discretionary_total: Money
    non_discretionary_total: Money
    avg_spend_per_meal: Money | None
    outliers: dict[str, str]  # description → reason
```

### 2. I/O Adapters (New)

- `src/io/equity.py` → `load_trades(path) → list[Trade]`
- `src/io/property.py` → `load_expenses(base_dir, fy, person) → list[PropertyExpense]`
- `src/io/reports.py` → `format_annual_summary(summary) → str` (console output)

### 3. Core Logic (New)

- `src/core/gains.py` → `calculate_capital_gains(trades, fy) → CapitalGainsSummary`
- `src/core/property.py` → `aggregate_expenses(expenses) → PropertyExpensesSummary`
- `src/core/wrap.py` → `generate_summary(txns, income, weights) → AnnualSummary`

### 4. Pipeline (Extend `src/pipeline.py`)

```python
def run_with_supplements(base_dir, fiscal_year):
    # Existing pipeline
    results = run(base_dir, fiscal_year)  # classify + deduce
    
    # Optional: add supplementary modules
    if Path(f"equity/{person}.csv").exists():
        trades = equity.load_trades(...)
        results[person]["gains"] = gains.calculate(trades, fiscal_year)
    
    if Path(f"archive/{fiscal_year}/{person}/property/").exists():
        expenses = property.load_expenses(...)
        results[person]["property"] = property.aggregate(expenses)
    
    # Wrap report (always available if txns exist)
    results[person]["wrap"] = wrap.generate_summary(txns, income, weights)
    
    return results
```

### 5. CLI (New Commands)

```bash
# Existing
taxing run --fy fy25

# New (optional)
taxing gains --fy fy25 --person tyson
taxing property --fy fy25 --person tyson
taxing wrap --fy fy25 --person tyson
```

---

## Testing Strategy for Ported Modules

### gains.py Tests

```python
def test_fifo_full_sell():
    """Sell entire lot from buffer."""
    trades = [Trade(buy, 100 units), Trade(sell, 100 units)]
    result = calculate(trades, 2025)
    assert result.trades_matched[0].units == 100
    assert result.gains_by_fy[2025] > 0

def test_loss_harvesting_prioritized():
    """Prefer loss-making lots over FIFO."""
    trades = [Trade(buy, 100 @ $50), Trade(buy, 100 @ $60), Trade(sell, 100 @ $55)]
    result = calculate(trades, 2025)
    # Should sell the $60 lot first (loss-making)
    assert result.trades_matched[0].profit < 0

def test_cgt_discount_applied():
    """Apply 50% discount for >365 day holds."""
    trades = [Trade(buy, 1 year ago, 100 @ $50), Trade(sell, today, 100 @ $60)]
    result = calculate(trades, 2025)
    # gain = profit/2 = (100 * 10) / 2 = $500
    assert result.gains_by_fy[2025] == Money(Decimal("500.00"), AUD)

def test_partial_sell_splits_lot():
    """Selling < holding amount splits lot + fee."""
    trades = [Trade(buy, 100 units, fee=$10), Trade(sell, 50 units)]
    result = calculate(trades, 2025)
    # Buffer should have 50 units with fee=$5
    assert result.buffer_remaining[0].units == 50
    assert result.buffer_remaining[0].fee == Decimal("5.00")

def test_efficiency_calculation():
    """Efficiency measures discount harvesting quality."""
    # If profit=$1000, all loss-harvested → gain=$500, efficiency=100%
    # If profit=$1000, no discount → gain=$1000, efficiency=0%
    pass
```

### property.py Tests

```python
def test_aggregate_four_categories():
    """Sum all four expense types."""
    expenses = [
        PropertyExpense("rent", Money(Decimal("2000"), AUD)),
        PropertyExpense("water", Money(Decimal("200"), AUD)),
        PropertyExpense("council", Money(Decimal("400"), AUD)),
        PropertyExpense("strata", Money(Decimal("300"), AUD)),
    ]
    result = aggregate(expenses)
    assert result.total == Money(Decimal("2900"), AUD)

def test_zero_expenses():
    """Handle empty expense list."""
    result = aggregate([])
    assert result.rent == Money(Decimal("0"), AUD)
    assert result.total == Money(Decimal("0"), AUD)

def test_missing_category():
    """Unknown category is skipped or raises."""
    expenses = [PropertyExpense("unknown", Money(Decimal("100"), AUD))]
    # Either: ignore and return zero, or raise ValueError
    pass
```

### wrap.py Tests

```python
def test_income_calculation():
    """Sum transactions in 'income' category."""
    txns = [
        Transaction(..., category={"income"}, amount=Money(Decimal("100000"), AUD)),
    ]
    result = generate_summary(txns, {}, 2025)
    assert result.income == Money(Decimal("100000"), AUD)

def test_pct_of_income_zero_income():
    """Handle division by zero."""
    result = generate_summary([], {}, 2025)
    # pct_of_income() should return "N/A" not crash
    assert result.income == Money(Decimal("0"), AUD)

def test_discretionary_vs_nondiscretionary():
    """Categorize food (non-d) vs entertainment (discretionary)."""
    txns = [
        Transaction(..., category={"grocery"}, amount=Money(Decimal("-100"), AUD)),
        Transaction(..., category={"entertainment"}, amount=Money(Decimal("-50"), AUD)),
    ]
    result = generate_summary(txns, {}, 2025)
    assert result.non_discretionary_total > result.discretionary_total

def test_obfuscated_detection():
    """Flag 'beem it' transactions."""
    txns = [
        Transaction(..., description="BEEM IT", category=None, amount=Money(Decimal("-50"), AUD)),
    ]
    result = generate_summary(txns, {}, 2025)
    assert "BEEM IT" in result.outliers
```

---

## Summary of Porting Effort

| Module | LOC (tax-og → taxing) | Tests | Hours | Risk | Priority |
|--------|------------------------|-------|-------|------|----------|
| 7_property.py | 30 → 15 | 8 | 2-3 | Low | Phase 1 |
| 5_wrap.py | 125 → 60 | 12 | 4-5 | Medium | Phase 2 |
| 6_gains.py | 150 → 80 | 15 | 6-8 | Medium-High | Phase 3 |
| **Total** | **305 → 155** | **35** | **12-16 hours** | - | - |

---

## Design Philosophy (Why This Porting Approach)

1. **Pure Functions over Imperative Scripts**
   - tax-og: Sequential side effects (print, mutate globals)
   - taxing: Functions with explicit I/O contracts (no hidden state)

2. **Immutable Data Structures**
   - tax-og: Pandas Series (mutable buffer modifications)
   - taxing: `@dataclass(frozen=True)` prevents accidental mutations

3. **Separation of Concerns**
   - tax-og: CSV read mixed with business logic
   - taxing: I/O adapters (`src/io/`) separate from core logic (`src/core/`)

4. **Testability First**
   - tax-og: Tied to filesystem (requires fixtures)
   - taxing: Pure functions testable with simple dataclass inputs

5. **Type Safety**
   - tax-og: Strings for amounts, categories (runtime errors)
   - taxing: `Money`, `Currency`, `set[str]` prevent type confusion

---

## Recommended Next Steps

1. **Immediate**: Implement `Phase 1 (property.py)` as proof-of-concept for porting pattern
2. **Short-term**: Add property + wrap to pipeline, enable optional CLI commands
3. **Medium-term**: Implement gains module (highest complexity, most valuable)
4. **Long-term**: Consider report generation (JSON export, web dashboard)

---

**Last Updated**: Oct 21, 2025  
**Prepared for**: Haiku architect (taxing project)  
**Reference**: tax-og @ `/Users/teebz/space/tax-og/src/pipeline/`
