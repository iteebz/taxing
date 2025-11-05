# Architecture Deep Dive: taxing

**Date**: 2025-11-05
**Reviewer**: Zealot Code Review
**Status**: 176 tests passing, -50 LOC ceremony purged

## Executive Summary

The taxing codebase is a well-tested (~3,500 LOC) Australian tax calculation system with solid domain logic but several architectural concerns:

1. **Ingestion**: Three implicit modes, memory-inefficient, slow DataFrame iteration
2. **Pipeline**: Monolithic orchestration function with no phase boundaries
3. **Config**: Premature optimization (deepcopy + cache for small config)
4. **Models**: Bloated Transaction (13 fields), mixed concerns
5. **Converters**: Business logic in I/O layer
6. **Persistence**: Fragile type handling, no schema validation
7. **Separation**: Unclear boundaries between core/io/lib

## Findings by Area

### 1. Converter Registry Pattern (src/io/converters.py)

**Current State:**
- Dual registries: BANK_REGISTRY (full config) + CONVERTERS (just functions)
- CONVERTERS filter is redundant (matches all keys anyway)
- Function-based converters with inconsistent signatures (beem requires extra param)

**Concerns:**
- Two validation paths (CONVERTERS vs BANK_REGISTRY checks)
- Business logic (currency conversion, sanitization) in I/O layer
- No formal interface for converters
- Hard to add new banks (must know implicit patterns)

**Recommendation:**
```python
@dataclass
class BankConfig:
    converter_fn: Callable
    fields: list[str]
    skiprows: int = 0
    requires_username: bool = False

BANKS = {
    "anz": BankConfig(anz, fields=[...]),
    "wise": BankConfig(wise, fields=[...]),
}
```

**Priority**: Medium
**Effort**: Low (1-2 hours)
**Risk**: Low (tests will catch issues)

---

### 2. Ingestion Architecture (src/io/ingest.py)

**Current State:**
- Three modes: flat (persons=None), nested (persons=[...]), year-aware
- Mode selection via optional parameter (implicit)
- Slow iteration: `for _, row in df.iterrows()`
- Loads all years into memory: `ingest_all_years()` returns full list

**Concerns:**
- Implicit behavior based on None vs list
- Two validation paths (CONVERTERS vs BANK_REGISTRY)
- Duplicated year extraction logic (fixed in ceremony purge)
- No streaming (memory: O(n_transactions * n_years))
- No error recovery (one bad row = entire file fails)
- Beem username inference re-reads CSV

**Recommendation:**
1. Extract directory discovery from ingestion
2. Use explicit mode parameter: `structure: Literal["flat", "nested", "year_aware"]`
3. Use vectorized operations instead of iterrows
4. Consider streaming for large datasets
5. Add error handling with partial ingest + warnings

**Priority**: High
**Effort**: Medium (4-6 hours)
**Risk**: Medium (must preserve behavior)

---

### 3. Config Structure (src/core/config.py)

**Current State:**
- Three functions all load entire YAML
- Deepcopy on every call (mutation safety)
- LRU cache on internal function (test pollution)
- Default path resolution duplicated in three places

**Concerns:**
- Wasteful: deepcopy entire config just to return one key
- Test pollution: lru_cache leaks between tests (fixed in test fixes)
- No validation of config structure
- FYConfig has dead fields (actual_cost_categories, fixed_rates)

**Recommendation:**
```python
@dataclass(frozen=True)
class ConfigRegistry:
    fy_configs: dict[int, FYConfig]
    deduction_groups: dict[str, list[str]]
    rate_basis_map: dict[str, str]

@lru_cache(maxsize=1)
def load_registry(config_path: Path) -> ConfigRegistry:
    raw = yaml.safe_load(config_path.read_text())
    # Parse once, return immutable structure
```

**Priority**: Medium
**Effort**: Low (2 hours)
**Risk**: Low (frozen dataclasses enforce immutability)

---

### 4. Domain Model (src/core/models.py)

**Current State:**
- Transaction: 13 fields mixing raw data + enrichment
- Frozen dataclasses with validation in __post_init__
- Property models: 4 identical classes (Rent, Water, Council, Strata)
- cats field is mutable set (should be frozenset)

**Concerns:**
- Transaction bloat: raw + dedup metadata + classification in one model
- Validation in __post_init__ is clunky (`object.__setattr__` to mutate frozen)
- No custom validation exceptions
- Property expense duplication (discussed in ceremony review)
- Individual model has domain logic (taxable_income calculation)

**Recommendation:**
1. Split Transaction: RawTransaction (from CSV) vs EnrichedTransaction (after pipeline)
2. Use Pydantic for validation (self-documenting, standard library)
3. Keep property expense split (type clarity > DRY)
4. Move calculations out of models (taxable_income → household.py)

**Priority**: Medium
**Effort**: Medium (3-4 hours, many test updates)
**Risk**: Medium (touches core abstractions)

---

### 5. Pipeline Architecture (src/pipeline.py)

**Current State:**
- Single 103-line run() function
- Orchestrates: ingest → dedupe → classify → validate → deduce → gains → persist
- No streaming, loads all into memory
- Returns metrics as magic dict with string keys

**Concerns:**
- Monolithic (hard to test phases in isolation)
- No checkpointing (failure = start over)
- No error recovery (one person fails = all fail)
- FY calculation duplicated inline
- Metrics computed inline with magic keys
- Audit runs after persist (can't fail based on alerts)

**Recommendation:**
```python
class TaxPipeline:
    def ingest(self) -> "TaxPipeline": ...
    def deduplicate(self) -> "TaxPipeline": ...
    def classify(self) -> "TaxPipeline": ...
    def validate(self) -> "TaxPipeline": ...
    def deduce(self) -> "TaxPipeline": ...
    def calculate_gains(self) -> "TaxPipeline": ...
    def persist(self) -> "TaxPipeline": ...

    def run(self) -> PipelineResult:
        return (self.ingest()
                    .deduplicate()
                    .classify()
                    .validate()
                    .deduce()
                    .calculate_gains()
                    .persist())
```

**Priority**: High
**Effort**: High (6-8 hours)
**Risk**: Medium (requires careful testing)

---

### 6. CSV Persistence (src/io/persist.py)

**Current State:**
- Match-based type serialization
- String manipulation to detect generic types (`str(field_type).startswith("set")`)
- No support for nested dataclasses
- Slow iteration: `for _, row in df.iterrows()`

**Concerns:**
- Type safety is weak (can't distinguish frozenset[str] from frozenset[int])
- Complex types fall back to str() (breaks round-trip)
- No schema validation (missing field = KeyError)
- Default values not handled (empty string → empty set, not None)
- frozenset round-trip broken (frozenset → set)

**Recommendation:**
```python
from pydantic import BaseModel

class TransactionModel(BaseModel):
    date: date
    amount: Decimal
    ...

def to_csv(objects: list[T], path: Path):
    df = pd.DataFrame([obj.model_dump() for obj in objects])
    df.to_csv(path)
```

**Priority**: Medium
**Effort**: Medium (4 hours)
**Risk**: Medium (serialization is critical)

---

### 7. Separation of Concerns

**Current State:**
- core/: Domain logic
- io/: Input/output
- lib/: Utilities
- Converters in io/ but contain business logic
- Config in core/ but loads YAML (infrastructure)
- Pipeline at top level (no application layer)

**Concerns:**
- Converters do domain work (currency conversion) in I/O layer
- Config does infrastructure work in core layer
- No orchestration layer (pipeline is orphaned)
- Lib has mixed responsibilities (paths=io, currency=core, sanitize=util)

**Recommendation:**
```
src/
├── app/            # Orchestration (pipeline)
├── domain/         # Pure logic (classify, deduce, gains)
├── infrastructure/ # I/O, config
│   ├── csv/        # CSV reading/writing
│   ├── bank_adapters/ # Bank converters
│   └── config/     # Config loading
└── utils/          # True utilities
```

**Priority**: Medium
**Effort**: High (8+ hours, major refactor)
**Risk**: High (requires careful dependency management)

---

## Recommended Refactoring Roadmap

### Phase 1: Quick Wins (2-4 hours)
1. ✅ **Purge ceremony** (DONE: -50 lines)
2. Consolidate config loading (single registry, no deepcopy)
3. Extract FY calculation helper (single source of truth)
4. Fix Transaction cats field (set → frozenset)

### Phase 2: Core Improvements (8-12 hours)
1. Unify ingestion modes (explicit structure parameter)
2. Extract pipeline phases (Pipeline class)
3. Replace persist serialization with Pydantic
4. Fix converter registry (BankConfig dataclass)

### Phase 3: Architecture (16+ hours)
1. Extract application layer (app/pipeline.py)
2. Clarify layer boundaries (domain vs infrastructure)
3. Consider streaming for large datasets
4. Add comprehensive error handling

---

## Test Strategy

All refactors must maintain:
- ✅ 176 tests passing
- ✅ Zero lint violations
- ✅ Contract tests for public APIs
- ✅ No behavior changes (unless fixing bugs)

---

## Conclusion

The codebase has **solid fundamentals**:
- Good test coverage (176 tests)
- Pure functions (classify, deduce)
- Immutability (frozen dataclasses)
- Type hints throughout

**Primary issues** are architectural:
- Implicit conventions (ingestion modes, config access)
- Premature optimization (deepcopy + cache)
- Monolithic orchestration (pipeline.run)
- Mixed concerns (converters in I/O)

**Recommended next steps**:
1. Fix config loading (Phase 1)
2. Extract pipeline phases (Phase 2)
3. Consider architectural refactor (Phase 3) only if extending significantly

The system works. Don't over-engineer unless pain points emerge in practice.
