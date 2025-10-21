# taxing context

## mission
Reference-grade, AI-agent-friendly tax deduction automation for Australian households.

## status (Oct 2025)

**Phase 1**: ✅ Complete (79 tests passing, zero lint)
- Transaction pipeline: ingest → classify → deduce → persist
- Multi-bank support (ANZ, CBA, Beem, Wise), 54 rule categories, configurable weights

**Phase 2a**: ✅ Complete (capital gains core)
- FIFO with loss harvesting + CGT discount (50% for holdings >365 days)
- Trade domain model (Trade, Gain dataclasses)
- Trade I/O converters (trades_to_csv, trades_from_csv, gains_to_csv, gains_from_csv)
- Ingestion (ingest_trades, ingest_trades_dir)
- Full pipeline integration (ingest → classify → deduce → **trades** → persist)
- Tests: 7 unit tests + 2 integration tests (parity, roundtrip)

**Phase 2b**: Next (bracket-aware sequencing, multi-year planning)

## entry point for new session

1. Read this file (1 min)
2. Run tests: `just test` (verify 79 pass)
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

- `src/core/trades.py` - FIFO + loss harvesting + CGT discount algorithm
- `src/core/models.py` - Trade, Gain, Money, Transaction dataclasses
- `src/io/persist.py` - CSV codec (trades, gains, transactions)
- `src/io/ingest.py` - Trade + transaction ingestion
- `src/pipeline.py` - Full orchestration
- `tests/unit/core/test_trades.py` - Trade logic unit tests
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

---

**Last Updated**: Oct 21, 2025 | **Tests**: 79 passing | **Lint**: Zero
