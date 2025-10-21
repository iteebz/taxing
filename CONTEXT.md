# TAXING: Zero-Ceremony Tax Deduction Automation

## Mission
Build a reference-grade, AI-agent-friendly tax deduction calculator for Australian household taxes. Port + modernize `tax-og` codebase with test-first architecture, pure functions, and explicit contracts.

## Current Status (Oct 2025)

### Completed
- **Core domain layer** (src/core/)
  - `models.py`: `Money`, `Transaction`, `Currency`, `AUD` types (immutable, type-safe)
  - `classify.py`: Pure function `classify(description, rules) → set[str]`
  - `deduce.py`: Pure function `deduce(txns, weights) → dict[str, Money]`
  - **Test coverage**: 26 tests, 100% coverage, zero lint
  - **Architecture**: Protocols (duck typing), no classes, immutable dataclasses

- **I/O layer** (src/io/)
  - `converters.py`: Pure bank→Transaction functions (ANZ, CBA, Beem, Wise)
    - Handles date parsing, description sanitization, multi-currency (Wise), Beem directionality
  - `ingest.py`: Load CSVs by bank + person, compose via `ingest_dir()`
    - Supports directory structure: `{base_dir}/{person}/raw/*.csv`
  - `persist.py`: CSV round-trip for transactions & weights
    - Handles empty txns, category serialization (comma-separated sets)
  - `config.py`: Immutable Config dataclass (env/file resolution, no globals)
  - **Test coverage**: 25 tests, 100% coverage, zero lint

- **Project structure**
  - Poetry, pytest, ruff, justfile (boilerplate from tax-og)
  - `.gitignore` (pycache, venv, .pytest_cache, .ruff_cache, .coverage, *.pyc)
  - tests/ mirrors src/ structure

### Next Steps (In Order)
1. **Rules system** (src/core/rules.py)
   - Load rules from `rules/*.txt` files into structured dict
   - Test: rule parsing, comment stripping, keyword matching

2. **Pipeline orchestration** (src/pipeline.py)
   - Compose: ingest → classify → deduce → persist
   - Dependency injection (no globals, no state)
   - Tests: integration/ full end-to-end

3. **CLI interface** (src/__main__.py or bin/)
   - Optional: `python -m taxing --fy fy25 --person tyson`
   - Leverage config + pipeline

## Mental Model

### Core Principles (GEMINI.md / ZEALOT.md)
- **Test-first**: No code without failing test
- **Protocols > Classes**: Use duck typing, minimal ceremony
- **Pure functions**: Logic has no I/O side effects
- **Immutability**: Types frozen, transactions immutable
- **Contracts as specs**: Tests define behavior, code implements

### Architecture Decisions
**Problem**: tax-og mixes I/O + logic, uses globals, hard to test/compose

**Solution**:
- `core/`: Pure domain logic (classify, deduce, models) - testable without filesystem
- `io/`: External I/O (bank CSVs, config, persistence) - I/O adapters only
- `pipeline/`: Orchestration (composition, dependency injection)
- No `conf.py` global state; config passed as argument

### Domain Model
```
Money(amount: Decimal, currency: Currency)
  - Type-safe arithmetic, prevents USD+AUD bugs
  - Immutable, auditable precision

Transaction(date, amount, description, source_bank, source_person, category?, is_transfer?)
  - Immutable transaction record
  - category: set[str] | None (None = unlabeled)

classify(description: str, rules: dict[str, list[str]]) → set[str]
  - Pure: no side effects
  - Case-insensitive substring matching
  - Returns empty set if no match

deduce(txns: list[Transaction], weights: dict[str, float]) → dict[str, Money]
  - Pure: applies weights (percentages) to categorized txns
  - Aggregates by category, handles multi-cat txns
  - Returns dict mapping category → deduction Money
```

### Test Strategy
- **Unit tests** (tests/unit/core/): Pure logic, no I/O
- **Integration tests** (tests/integration/): Full pipeline, mock I/O
- **Fixtures**: conftest.py for reusable test data
- **Coverage metric**: aim for 90%+, test contracts not implementation

## Key Files

### Codebase
- `src/core/models.py`: Type definitions
- `src/core/classify.py`: Classification logic
- `src/core/deduce.py`: Deduction calculation
- `tests/unit/core/`: Tests for core logic
- `pyproject.toml`: Poetry config (pandas, pytest, ruff)
- `justfile`: Make-like commands (test, lint, format, etc.)

### Reference (tax-og)
- `tax-og/docs/context.md`: Original architecture overview
- `tax-og/src/pipeline/1_ingest.py`: Bank converters (template)
- `tax-og/src/utils/cats.py`: Rule loading (template)
- `tax-og/rules/`: 50+ category rule files

## Important Context

### tax-og Challenges (Why Refactor)
1. **Global state**: `conf.py` loaded at import time, hard to test
2. **I/O tangled with logic**: CSV read/write mixed with calculations
3. **Imperative scripts**: Sequential steps (1_ingest.py → 2_label.py), hard to compose
4. **No type safety**: Strings everywhere, easy to mix AUD+USD or forget categories
5. **Opaque rules**: Text files, hard for agents to reason about

### What Works in tax-og (Keep)
1. **Rule-based classification**: String matching is simple + auditable (vs ML)
2. **Multi-person, multi-year**: Supports couples, historical data
3. **Percentage-based deductions**: Defensible (explicit, traceable)
4. **Pipeline stages**: CSV checkpoints allow inspection, reruns, debugging

### Known Issues (Tax Law)
1. **International transactions**: Currently dropped (lost deductions)
2. **High percentages** (>60%): May trigger ATO attention
3. **Duplicate handling**: Weak, can amplify deductions
4. **Transfer detection**: Needed to exclude internal P2P transfers

## Continuation Notes

### For Fresh Haiku Session
1. **Start here**: Read CONTEXT.md (2 min)
2. **Current state**: Core domain + I/O layer complete, 94% coverage (51 tests)
3. **Next work**: Rules system (load `.txt` files), then pipeline orchestration
4. **Command**: `just test` to verify all 51 tests pass

### Common Tasks
```bash
# Run tests
just test

# Check coverage
just cov

# Lint + format
just lint
just format

# Full CI
just ci
```

### Data Flow (After Complete)
```
raw/fy25/{person}/*.csv
    → ingest (convert bank formats)
    → classify (match rules)
    → deduce (apply weights)
    → deductions.csv
```

### Test Coverage Target
- Core domain: 100% (pure logic, no excuses)
- I/O adapters: 80%+ (some bank formats may need manual inspection)
- Integration: 70%+ (pipeline composition)

## Agent-Friendly Notes
- **Modularity**: Each function is small, testable, composable
- **No magic**: Pure functions, explicit arguments, clear returns
- **Type hints**: Full coverage, enables IDE support + type checking
- **Immutability**: Prevents accidental mutations, easier to reason about
- **Contracts**: Protocols define behavior, agents can verify compliance

---

**Last Updated**: Oct 21, 2025
**Model**: claude-haiku-4-5 (session 2)
**Status**: Core + I/O complete (94% coverage), rules system next
