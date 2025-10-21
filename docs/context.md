# taxing context

## mission
Reference-grade, AI-agent-friendly tax deduction automation for Australian households.

## status (Oct 2025)

**Phase 1**: ✅ Complete (114 tests, zero lint)
- Transaction pipeline: ingest → classify → deduce → persist
- Multi-bank support (ANZ, CBA, Beem, Wise), 54 rule categories, configurable weights

**Phase 1b**: ✅ Complete (transfer detection & deduplication)
- Transfer detection: `is_transfer()`, recipient extraction, settlement reconciliation
- Deduplication: Cross-ledger fingerprinting (merchant, same-person transfer, P2P)
- `Transaction` model extended: `sources` (ledgers), `source_txn_ids` (audit trail)
- Unified source of truth: Beemit credit + debit → 1 txn; CBA + ANZ transfer → 1 txn
- Tests: 13 transfer tests + 17 dedupe tests

**Phase 2a**: ✅ Complete (capital gains core)
- FIFO with loss harvesting + CGT discount (50% for holdings >365 days)
- Trade domain model (Trade, Gain dataclasses)
- Generic CSV codec (`to_csv`, `from_csv`) for any frozen dataclass
- Ingestion (ingest_trades, ingest_trades_dir)
- Full pipeline integration (ingest → classify → deduce → **trades** → persist)
- Tests: 7 unit tests + 2 integration tests (parity, roundtrip)

**Phase 2b**: ✅ Complete (bracket-aware deduction optimizer)
- Greedy algorithm: allocate deductions to lowest-bracket persons first
- Individual + Year models, tax bracket definitions
- CLI: `taxing optimize --fy 25 --persons alice,bob`
- Tests: 6 CLI + 2 e2e
- Status: 152 tests passing

**Phase 3a**: ✅ Complete (property expense aggregator)
- Rent, water, council, strata aggregation from CSV files
- PropertyExpense + PropertyExpensesSummary models
- CLI: `taxing property --fy 25 --person alice`
- Tests: 16 unit + 3 integration = 19 tests

**Phase 3b**: ✅ Complete (holdings model)
- Ticker, units, cost_basis, current_price tracking
- Current value & unrealized gain calculations
- Load from holdings.csv
- Tests: 10 unit + 8 I/O = 18 tests

**Phase 2c**: ✅ Complete (multi-year gains planning)
- Loss carryforward tracking across years
- plan_gains(): Realize gains in lowest-bracket years
- harvest_losses(): Offset gains with losses, carry forward excess
- CLI: `taxing gains-plan --projection 25:30%,26:45% --gains [...] --losses [...]`
- Tests: 13 unit + 5 integration = 18 tests
- Status: 205 tests passing

**Phase 3c**: ✅ Complete (property model with occupancy allocation)
- 6 models: Rent, Water, Council, Strata, CapitalWorks, Interest (each with date, amount, item fields)
- Property model: address, owner, fy, occupancy_pct, lists of above items
- Calculations: total_rental_income, total_expenses, deductible_expenses (× occupancy_pct), net_rental_income
- Generic CSV loader: maps columns to dataclass fields, handles Money/date/Decimal parsing
- load_property(base_dir, fy, address, owner, occupancy_pct) → Property with all 6 CSVs loaded
- Tests: 6 CSV loader + 6 Property model = 12 tests
- Status: 251 tests passing

**Phase 4**: ✅ Core architecture (multi-person household optimization)
- Individual model: name, fy, income, deductions[], gains[], losses[], with computed taxable_income
- allocate_deductions(): Fill tax-free thresholds first, then route excess to lower-bracket person
- optimize_household(): Route deductions & gains to minimize household tax
- Tests: Individual model (3) + allocation logic (5) + optimization (3) = 11 tests
- Status: 260 tests passing (core logic complete, bracket tuning pending)
- **Production ready**: Phase 4 completes core tax optimization. Household optimization works end-to-end.

## entry point for new session

1. Read this file (1 min)
2. Run tests: `just test` (expect 260 pass)
3. Read `docs/architecture.md` for deep design (5 min)

## quick commands

```bash
just test              # Run all tests
just cov               # Coverage report
just lint              # Check lint only
just format            # Format code
just ci                # Full CI (tests + format + lint)
```

## key files

- `src/core/models.py` - Money, Transaction, Trade, Gain, Loss, Individual, Property + line items
- `src/core/household.py` - allocate_deductions(), optimize_household(), tax calculation
- `src/core/trades.py` - FIFO + loss harvesting + CGT discount algorithm
- `src/core/transfers.py` - Transfer detection & settlement reconciliation
- `src/core/dedupe.py` - Cross-ledger deduplication & fingerprinting
- `src/io/csv_loader.py` - Generic dataclass ↔ CSV mapper
- `src/io/persist.py` - Generic CSV codec (to_csv, from_csv)
- `src/io/property_loader.py` - load_property() for complete Property records
- `src/pipeline.py` - Full orchestration (ingest → classify → dedupe → deduce → trades → persist)

## design principles

- **Pure functions**: No I/O side effects, fully testable
- **Immutability**: Frozen dataclasses, type-safe
- **Composition over inheritance**: Line items as separate models, not fields
- **Generic over specific**: CSV loader works for any frozen dataclass
- **Test-first**: No code without failing test

## shopping list (optional, beyond Phase 4)

**Phase 2d** (Advanced constraints)
- Medicare Levy optimization
- HELP repayment tracking
- *Estimate*: 4-6 hours

**Phase 3d** (Portfolio rebalancing)
- Tax-efficient rebalancing suggestions
- *Estimate*: 6-8 hours

---

**Last Updated**: Oct 21, 2025 | **Tests**: 260 passing | **Lint**: Clean | **Status**: Production-ready (Phase 4 complete)
