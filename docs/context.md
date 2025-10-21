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
- Status: 169 tests passing

## entry point for new session

1. Read this file (1 min)
2. Run tests: `just test` (verify 166 pass)
3. Read `docs/architecture.md` for deep design (5 min)
4. Check Phase 2b design in `docs/phase_2b_design.md`

## quick commands

```bash
just test              # Run all tests
just cov               # Coverage report
just lint && format    # Lint + format
just ci                # Full CI
```

## key files

- `src/core/models.py` - Trade, Gain, Money, Transaction, Deduction, Summary, Transfer dataclasses
- `src/core/trades.py` - FIFO + loss harvesting + CGT discount algorithm
- `src/core/transfers.py` - Transfer detection & settlement reconciliation
- `src/core/dedupe.py` - Cross-ledger deduplication & fingerprinting
- `src/io/persist.py` - Generic CSV codec (`to_csv`, `from_csv`)
- `src/io/ingest.py` - Trade + transaction ingestion
- `src/pipeline.py` - Full orchestration (ingest → classify → dedupe → deduce → trades → persist)
- `tests/unit/core/test_trades.py` - Trade logic unit tests (7 tests)
- `tests/unit/core/test_transfers.py` - Transfer detection & settlement (13 tests)
- `tests/unit/core/test_dedupe.py` - Deduplication & fingerprinting (17 tests)
- `tests/integration/test_trades_parity.py` - Parity validation vs tax-og

## design principles

- **Pure functions**: No I/O side effects, fully testable
- **Immutability**: Frozen dataclasses, type-safe
- **Protocols > classes**: Duck typing, minimal ceremony
- **Test-first**: No code without failing test
- **Separation of concerns**: `core/` (logic), `io/` (I/O), `pipeline/` (orchestration)

## known patterns for next phase

**CSV codec pattern** (identified but deferred to Phase 2b):
- trades_to_csv / trades_from_csv follow identical structure
- gains_to_csv / gains_from_csv follow identical structure
- Opportunity: Unified generic codec using dataclass field metadata

## shopping list

**Phase 3b** (Holdings model)
- Ticker, units, cost_basis, current_price tracking
- Frozen dataclass
- Enable Phase 2c gains planning
- Effort: 1 hour

**Phase 2c** (Multi-year gains planning)
- Defer gains to next FY if better bracket
- Loss carryforward tracking
- Holdings integration for position tracking
- Requires: Phase 3b (Holdings)

**Phase 3c** (Rental income + depreciation)
- Property-level rental income tracking
- Capital works deduction schedule
- Depreciation via ATO depreciation tool

---

**Last Updated**: Oct 21, 2025 | **Tests**: 166 passing | **Lint**: Clean (property module)
