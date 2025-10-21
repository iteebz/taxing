# taxing documentation

Reference-grade tax deduction automation for Australian households.

## entry points

**First visit?** (10 mins)
1. [context.md](context.md) - Status, commands, test counts
2. [models.md](models.md) - All dataclasses
3. [algorithms.md](algorithms.md) - Core logic

**Reference docs**:
- [Architecture](architecture.md) - System design, I/O patterns
- [Tax calculations](tax.md) - Bracket math, optimization
- [Phases](phases.md) - Progress, limitations

| Doc | Content |
|-----|----------|
| [context.md](context.md) | Status, commands, entry points |
| [models.md](models.md) | Dataclasses, validation |
| [algorithms.md](algorithms.md) | FIFO, loss harvesting, tax rates, deduction allocation |
| [tax.md](tax.md) | Bracket math, household optimization |
| [architecture.md](architecture.md) | System design, I/O patterns |
| [phases.md](phases.md) | Phase 1-4 status, limitations |
| [ingestion.md](ingestion.md) | CSV formats, directory structure |

## key principles

- **Pure functions**: No I/O side effects, fully testable
- **Immutability**: Frozen dataclasses prevent mutation bugs
- **Composition over inheritance**: Line items as separate models
- **Type safety**: Decimal + Money prevent silent arithmetic bugs
- **Test-first**: No code without failing test

---

**Latest update**: Oct 21, 2025 | **Status**: Production-ready (Phase 4 complete)
