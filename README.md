# taxing

Reference-grade tax deduction automation for Australian households.

Ingests bank & trading platform data, classifies transactions, calculates deductions, and optimizes capital gains sequencing across tax brackets.

## Quick Start

```bash
# Test
just test

# Lint + format
just lint
just format

# Full CI
just ci
```

## Structure

```
src/
  core/          Pure domain logic (classify, deduce, capital gains)
  io/            I/O adapters (bank converters, ingest, persist)
  pipeline.py    Orchestration (ingest → classify → deduce)
  cli/           CLI entry points

docs/
  context.md              Active session entry point
  architecture.md         Deep design reference (principles, patterns, data flow)
  phase_2b_design.md      Phase 2b bracket-aware sequencing design
  TAX_OG_PORTING_ANALYSIS.md  Feature comparison with tax-og

rules/
  *.txt           Rule files for classification (54 categories)

tests/
  unit/           Pure logic tests
  integration/    Full pipeline tests
```

## Architecture

**Phase 1** (complete): Transaction pipeline
- Ingest: Multi-bank support (ANZ, CBA, Beem, Wise)
- Classify: Rule-based categorization (54 categories)
- Deduce: Percentage-based deductions
- Persist: CSV outputs (transactions, deductions, summary)
- **Status**: 114 tests, zero lint

**Phase 2a** (complete): Capital gains core
- FIFO with loss harvesting prioritization
- CGT discount (50% for holdings >365 days)
- Trade ingestion (ingest_trades, ingest_trades_dir)
- Integrated into pipeline
- **Status**: 29 tests, parity validated vs tax-og

**Phase 2b** (complete): Bracket-aware deduction optimizer
- Greedy algorithm: allocate to lowest-bracket persons first
- CLI: `taxing optimize --fy 25 --persons alice,bob`
- Reads Phase 1 outputs (deductions per person)
- Pools and optimally allocates to minimize total tax
- See `docs/phase_2b_cli.md`
- **Status**: 8 tests

**Phase 3a** (complete): Property expense aggregator
- Aggregates rent, water, council, strata from CSV files
- CLI: `taxing property --fy 25 --person alice`
- PropertyExpensesSummary with category totals
- See `docs/phase_3a_property.md`
- **Status**: 19 tests

**Phase 3b** (complete): Holdings model
- Ticker, units, cost_basis, current_price
- Current value & unrealized gain properties
- Load from holdings.csv
- Supports fractional & large positions
- **Status**: 18 tests

**Phase 2c** (complete): Multi-year capital gains planning
- Loss carryforward tracking indefinitely across years
- Realize gains in lowest-bracket years first
- Harvest losses to offset current & future gains
- CLI: `taxing gains-plan --projection 25:30%,26:45% --gains [...] --losses [...]`
- **Status**: 18 tests, 205 tests total

## Data Model

```python
Money(amount: Decimal, currency: Currency)
Transaction(date, amount, description, source_bank, source_person, category?, is_transfer?)
Trade(date, code, action, units, price, fee, source_person)
Gain(fy, raw_profit, taxable_gain, action)
```

Type-safe, immutable, no silent bugs. See `docs/architecture.md` for full details.

## Design Principles

- **Pure functions**: No side effects, testable without I/O
- **Immutability**: Frozen dataclasses, prevents accidental mutations
- **Contracts**: Protocols define behavior, tests verify compliance
- **No globals**: Config passed as arguments
- **Agent-friendly**: Modular, type-hinted, well-tested

## Next Steps

1. Phase 3c: Rental income + depreciation tracking
2. Phase 2d: Advanced constraints (Medicare Levy, HELP, ILP)
3. Phase 3d: Portfolio rebalancing optimization

See `docs/context.md` for quick reference, `docs/architecture.md` for deep design.
