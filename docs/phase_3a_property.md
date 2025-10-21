# Phase 3a: Property Expense Aggregator

## Overview

The `taxing property` command aggregates investment property expenses (rent, water, council rates, strata/body corp fees) from CSV files and produces a summary.

## Setup

### Directory Structure

Create property expense CSVs at:

```
archive/{fy}/{person}/property/
  ├── rent.csv
  ├── water.csv
  ├── council.csv
  └── strata.csv
```

Each CSV is simple: one amount per row, one per line.

### Example CSV Format

**rent.csv:**
```
2000
2000
```

**water.csv:**
```
100
100
```

**council.csv:**
```
200
200
```

**strata.csv:**
```
150
150
```

## Usage

### Basic Usage

```bash
python taxing property --fy 25 --person alice
```

### With Custom Base Directory

```bash
python taxing property --fy 25 --person alice --base-dir /path/to/data
```

## Output

```
Property Expenses - alice FY25
--------------------------------------------------
Rent                      $4,000.00
Water                       $200.00
Council Rates               $400.00
Strata/Body Corp            $300.00
--------------------------------------------------
TOTAL                     $4,900.00
```

## Features

- **Simple CSV format**: One amount per line, no headers required
- **Graceful degradation**: Missing categories return zero
- **Comment support**: Lines starting with `#` are skipped
- **Error resilience**: Invalid amounts are silently skipped
- **Decimal precision**: All amounts use Decimal for precision
- **Multi-entry support**: Multiple entries per category sum correctly

## Data Model

```python
@dataclass(frozen=True)
class PropertyExpense:
    expense_type: str  # "rent", "water", "council", "strata"
    amount: Money

@dataclass(frozen=True)
class PropertyExpensesSummary:
    rent: Money
    water: Money
    council: Money
    strata: Money

    @property
    def total(self) -> Money:
        return self.rent + self.water + self.council + self.strata
```

## Integration

Property expenses can be integrated into tax planning workflows:

1. **Phase 2b (Deduction Optimizer)**: Can allocate property expenses to lowest-bracket person
2. **Phase 2c (Multi-year Planning)**: Track property expenses across years
3. **Phase 3c (Depreciation)**: Coordinate with capital works deductions

## API

### Core Logic

```python
from src.core.property import aggregate_expenses
from src.io.property import load_property_expenses

# Load from CSV files
expenses = load_property_expenses(base_dir, fy=25, person="alice")

# Aggregate by category
summary = aggregate_expenses(expenses)

print(f"Total: ${summary.total.amount:,.2f}")
```

### CLI

```bash
taxing property --fy 25 --person alice [--base-dir .]
```

## Testing

16 tests cover:
- Single/multiple category aggregation
- All four categories
- Multiple entries per category
- Empty lists and zero amounts
- Unknown category handling
- Decimal precision
- CSV loading with comments
- Invalid amount skipping
- Missing directories

Run: `just test`

## Future Extensions

1. **Multiple properties**: Support multiple property locations per person
2. **Category breakdown**: Separate rent by room/tenant
3. **Depreciation integration**: Schedule capital works deductions
4. **Multi-year tracking**: Analyze expense trends across years
5. **Benchmarking**: Compare to average for postcode/property type
