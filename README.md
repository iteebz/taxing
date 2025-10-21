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
- Classify: Rule-based categorization
- Deduce: Percentage-based deductions
- Persist: CSV outputs (transactions, deductions, summary)
- **Status**: 79 tests passing, zero lint

**Phase 2a** (complete): Capital gains core
- FIFO with loss harvesting prioritization
- CGT discount (50% for holdings >365 days)
- Trade ingestion (ingest_trades, ingest_trades_dir)
- Integrated into pipeline
- **Status**: 79 tests passing, parity validated vs tax-og

**Phase 2b** (next): Bracket-aware sequencing
- Tax bracket awareness
- Multi-year planning
- Loss carryforward tracking
- See `docs/phase_2b_design.md`

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

1. Phase 2b: Bracket-aware sequencing (maximize tax efficiency across income levels)
2. Phase 2c: Multi-year capital gains planning (defer gains to better brackets)
3. Phase 2d: Advanced constraints (Medicare Levy, HELP repayment, ILP optimization)

See `docs/context.md` for quick reference, `docs/architecture.md` for deep design.
