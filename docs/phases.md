# phase progress & known limitations

## phase 1: transaction pipeline ✅

**Status**: Complete | **Tests**: 54 unit + 20 integration | **Lines**: ~400

### Deliverables

- Bank CSV ingest (ANZ, CBA, Beem, Wise)
- Transaction classification (keyword rules, case-insensitive matching)
- Deduction inference (weighted category allocation)
- CSV persistence (roundtrip serialization)

### Key functions

- `ingest_dir()` - Load all transactions from archive
- `classify()` - Keyword rule matching
- `deduce()` - Apply category weights
- `persist()` - Save to CSV with audit trail

### Known limitations

1. **International transactions**: Multi-currency dropped (AUD conversion complex)
2. **High percentages** (>60%): May trigger ATO attention (risk flag, not enforced)
3. **Duplicate detection**: Weak (can amplify same deduction across ledgers)
4. **Transfer detection**: Incomplete (P2P transfers not fully excluded)

**Mitigation**: Cross-ledger fingerprinting added in Phase 1b (transfer detection improved).

---

## phase 1b: transfer detection & deduplication ✅

**Status**: Complete | **Tests**: 13 transfer + 17 dedupe | **Lines**: ~250

### Deliverables

- Cross-ledger transfer detection (recipient extraction, settlement reconciliation)
- Deduplication fingerprinting (merchant, person, P2P)
- Unified source of truth (Beemit credit+debit → 1 txn; CBA+ANZ transfer → 1 txn)
- Audit trail (source_txn_ids for traceability)

### Key functions

- `is_transfer()` - Identify cross-ledger moves
- `extract_recipient()` - Parse transfer destination
- `fingerprint()` - Cross-ledger reconciliation
- `dedupe()` - Merge duplicate transactions

### Known limitations

1. **Manual recipient matching**: User must confirm transfer recipients (not automated)
2. **P2P transfers**: Still require manual deduplication (heuristics too error-prone)

---

## phase 2a: capital gains & FIFO ✅

**Status**: Complete | **Tests**: 7 unit + 2 integration (parity) | **Lines**: ~180

### Deliverables

- Trade ingestion (buy/sell records with dates, prices, fees)
- FIFO with loss harvesting (priority: loss > discount > FIFO)
- CGT discount (50% if held >365 days)
- Generic CSV codec (any frozen dataclass ↔ CSV)

### Key functions

- `process_trades()` - FIFO + loss harvesting + CGT discount
- `gains_to_csv()` / `gains_from_csv()` - Gain serialization
- `trades_to_csv()` / `trades_from_csv()` - Trade serialization

### Known limitations

1. **Bracket-unaware**: No consideration of tax bracket headroom (Phase 2b)
2. **No multi-year planning**: Can't defer gains to better bracket year
3. **No loss carryforward**: Can't track unused losses from prior years (Phase 2c adds this)
4. **Crypto not tested**: Placeholder support, no real test fixtures

**Parity test**: Verified against tax-og (real FY25 data, 200+ trades).

---

## phase 2b: bracket-aware deduction optimizer ✅

**Status**: Complete | **Tests**: 6 unit + 2 e2e | **Lines**: ~120

### Deliverables

- Individual model (income, deductions, gains, losses)
- Year model with tax brackets (FY25 AUD)
- Greedy optimizer (allocate deductions to lowest-bracket persons first)
- CLI: `taxing optimize --fy 25 --persons tyson,janice`

### Key functions

- `optimize()` - Route deductions by bracket
- `tax_liability()` - Progressive tax calculation
- `marginal_rate()` - Get current bracket

### Known limitations

1. **Two-person hardcoded**: Optimizer assumes exactly 2 people (Tyson & Janice)
2. **No multi-year optimization**: Can't defer deductions across years
3. **No constraint satisfaction**: Doesn't handle minimum tax thresholds (Medicare Levy, HELP)

---

## phase 2c: multi-year gains planning ✅

**Status**: Complete | **Tests**: 13 unit + 5 integration | **Lines**: ~150

### Deliverables

- Loss carryforward tracking (FY24 losses → FY25+)
- Multi-year planning (realize gains in lowest-bracket years)
- Loss harvesting (offset gains with losses, carry forward excess)
- CLI: `taxing gains-plan --projection 25:30%,26:45% --gains [...] --losses [...]`

### Key functions

- `plan_gains()` - Realize gains in optimal years
- `harvest_losses()` - Offset gains with carryforwards

### Known limitations

1. **Static bracket projection**: User must provide bracket guesses (no forecasting)
2. **No reinvestment**: Can't track capital redeployed after harvest

---

## phase 3a: property expense aggregator ✅

**Status**: Complete | **Tests**: 16 unit + 3 integration | **Lines**: ~100

### Deliverables

- Property expense aggregation (rent, water, council, strata)
- PropertyExpense + PropertyExpensesSummary models
- CSV loading from archive structure
- CLI: `taxing property --fy 25 --person tyson`

### Key functions

- `load_property_expenses()` - Aggregate expense CSVs
- `Property` model with `net_rental_income` calculation

### Known limitations

1. **Occupancy allocation**: Manual `occupancy_pct` input (not auto-detected)
2. **Capital works depreciation**: Not calculated (future phase)
3. **Interest tracking**: Loaded but not integrated into deductions

---

## phase 3b: holdings model ✅

**Status**: Complete | **Tests**: 10 unit + 8 I/O | **Lines**: ~80

### Deliverables

- Holding model (ticker, units, cost_basis, current_price)
- Current value & unrealized gain calculations
- CSV loading (holdings.csv)

### Key functions

- `load_holdings()` - Load portfolio from CSV
- `Holding.current_value` - Calculate market value
- `Holding.unrealized_gain` - Calculate unrealized P&L

### Known limitations

1. **No dividend tracking**: Holdings model doesn't track income distributions
2. **No rebalancing suggestions**: Holdings are read-only (no recommendations)

---

## phase 3c: property model with occupancy ✅

**Status**: Complete | **Tests**: 12 unit | **Lines**: ~150

### Deliverables

- 6 line-item models: Rent, Water, Council, Strata, CapitalWorks, Interest (each with date, amount, item fields)
- Property aggregator model (address, owner, fy, occupancy_pct)
- Generic CSV loader (maps columns to dataclass fields, handles Money/date/Decimal parsing)
- Property calculations (total_rental_income, deductible_expenses, net_rental_income)

### Key functions

- `load_csv()` - Generic dataclass ↔ CSV mapper
- `load_property()` - Complete property record from all 6 CSVs
- `Property.net_rental_income` - Calculate deductible net income

### Known limitations

1. **Single occupancy percent**: Assumes constant occupancy throughout year (monthly variance not supported)
2. **No capital works depreciation**: CapitalWorks loaded but not amortized (Phase 3d)
3. **Interest tracking**: Interest rows loaded, but not automatically deducted (manual allocation needed)

---

## phase 4: household optimization ✅

**Status**: Production ready | **Tests**: 11 unit + 0 integration | **Lines**: ~150

### Deliverables

- Individual model (name, fy, income, deductions[], gains[], losses[])
- `allocate_deductions()` - Fill tax-free thresholds first, route excess to lower-bracket person
- `optimize_household()` - Consolidate deductions to minimize household tax
- Tax calculation functions (bracket lookup, liability calculation)

### Key functions

- `allocate_deductions()` - Two-phase deduction allocation (threshold-fill + bracket-route)
- `optimize_household()` - Compare marginal rates, consolidate to lower-bracket person
- `_tax_liability()` - Progressive tax calculation
- `_tax_rate()` - Marginal rate lookup

### Core algorithm

**Phase 1**: Fill tax-free thresholds first (preserves bracket space)
**Phase 2**: Route remaining deductions to lower-bracket person

Example (FY25):
- Tyson: $0 income, buffer = $18,200
- Janice: $50,000 income, buffer = $0
- Deductions available: $10,000
- Allocation: All $10,000 to Tyson (fills his threshold first)

**Why**: Tyson's threshold is available and valuable (any future income will be at his rate). Janice's threshold is exhausted (her income is above $18,200).

### Known limitations

1. **Two-person hardcoded**: `optimize_household(yours, janice)` assumes exact names
2. **No multi-year deduction carry**: Can't defer deductions to future years
3. **No constraint satisfaction**: Doesn't handle Medicare Levy cliffs, HELP thresholds
4. **No loss routing**: Gains always stay with original owner (Phase 4b could optimize)

### Test coverage

- Individual model tests (3)
- Allocation tests (5)
- Optimization tests (3)
- Total: 11 tests passing, 263 total suite

---

## optional: phase 2d (advanced constraints)

**Not started** | **Estimate**: 4-6 hours

### Scope

- Medicare Levy (2% on income, cliff at $280k for singles)
- HELP repayment (10% of income above $56k)
- Combined optimization (bracket + levy + HELP)

### Complexity

- 3 independent tax systems stacked on top of progressivity
- Non-linear optimization (may require scipy.optimize)
- Real-world risk: Misunderstanding HELP caps → audit exposure

---

## optional: phase 3d (portfolio rebalancing)

**Not started** | **Estimate**: 6-8 hours

### Scope

- Tax-efficient rebalancing suggestions
- Capital gains forecasting (when to sell for tax loss harvesting)
- Dividend reinvestment tracking

### Complexity

- Requires market data (price history)
- Loss harvesting timing (wash sale rules, AU-specific)
- User communication (recommendations, not just data)

---

## architecture health

| Metric | Status | Notes |
|--------|--------|-------|
| Test coverage | ✅ 263 tests | Pure functions, 100% unit test coverage goal |
| Lint | ✅ Clean | Type-safe, no warnings |
| Code style | ✅ Zealot-grade | Minimal names, zero comments unless essential |
| Documentation | ✅ Reference-grade | Models, algorithms, tax calculations all documented |
| Performance | ✅ Sub-1s | Full test suite runs in 0.64s |
| Production readiness | ✅ Phase 4 complete | Household optimization end-to-end working |

---

**Last Updated**: Oct 21, 2025
