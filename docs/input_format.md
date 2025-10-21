# Input Format Reference

## Directory Structure

```
data/
├── fy23/
│   ├── alice/
│   │   ├── raw/
│   │   │   ├── cba.csv
│   │   │   ├── anz.csv
│   │   │   ├── beem.csv
│   │   │   └── wise.csv
│   │   └── trades.csv
│   ├── bob/
│   │   ├── raw/
│   │   │   └── cba.csv
│   │   └── trades.csv
├── fy24/
│   └── (same structure)
├── fy25/
│   └── (same structure)
├── weights.csv
└── rules/
    ├── groceries.txt
    ├── transport.txt
    └── ...
```

## Bank CSV Formats

### CBA (Commonwealth Bank)
**File**: `{person}/raw/cba.csv`
**Columns**: `date_raw, amount, description_raw, balance`

```csv
01/01/2023,100.00,WOOLWORTHS CHECKOUT,5000.00
02/01/2023,-50.00,TRANSFER TO ANZ,4950.00
```

### ANZ (Australia and New Zealand Banking)
**File**: `{person}/raw/anz.csv`
**Columns**: `date_raw, amount, description_raw`

```csv
01/01/2023,100.00,WOOLWORTHS CHECKOUT
02/01/2023,-50.00,TRANSFER FROM CBA
```

### Beem (P2P Transfer App)
**File**: `{person}/raw/beem.csv`
**Columns**: `datetime, type, reference, amount_str, payer, recipient, message`
**Note**: Requires beem username config (see Config section)

```csv
01/01/2023 14:30:00,credit,ref001,100.00,alice,bob,lunch money
02/01/2023 15:45:00,debit,ref002,50.00,bob,charlie,drinks
```

### Wise (International Transfers)
**File**: `{person}/raw/wise.csv`
**Columns**: `id, status, direction, created_on, finished_on, source_fee_amount, source_fee_currency, target_fee_amount, target_fee_currency, source_name, source_amount_after_fees, source_currency, target_name, target_amount_after_fees, target_currency, exchange_rate, reference, batch`

```csv
tf_abc123,completed,outgoing,2023-01-01T10:00:00Z,2023-01-01T10:05:00Z,5.00,AUD,2.50,USD,Bob,5000.00,AUD,Alice,3100.00,USD,0.62,bill_split,batch_001
```

## Trades CSV Format

**File**: `{person}/trades.csv`
**Columns**: `date, code, action, units, price, fee`

```csv
date,code,action,units,price,fee
2023-01-15,ASX:BHP,buy,100.0,30.00,10.00
2024-08-20,ASX:BHP,sell,50.0,50.00,15.00
2024-12-10,ASX:NAB,buy,20.0,35.00,10.00
```

## Weights CSV Format

**File**: `weights.csv` (optional, at root)
**Columns**: `category, weight`
**Purpose**: Controls deduction allocation confidence (higher = prioritized)

```csv
category,weight
groceries,0.8
transport,0.7
medical,0.9
entertainment,0.2
```

## Rules Directory

**Location**: `rules/`
**Format**: One merchant pattern per line
**Purpose**: Classification patterns for transaction categorization

Example `rules/groceries.txt`:
```
COLES
WOOLWORTHS
ALDI
IGA
```

Example `rules/transport.txt`:
```
UBER
LYFT
TAXI
BUS
```

## Notes

1. **Date Formats**:
   - Bank CSVs: `DD/MM/YYYY` (parsed by converters)
   - Trades CSV: `YYYY-MM-DD`
   - Beem: ISO8601 datetime

2. **Amounts**:
   - All amounts in AUD (Decimal precision preserved)
   - Negative = debit/outgoing, Positive = credit/incoming
   - Fees stored separately for trades

3. **Multi-Year Pipeline**:
   - Run pipeline separately for each FY (fy23, fy24, fy25)
   - Output persisted to `{person}/data/` directory
   - Transfers reconciled across all persons in single run

4. **Persons**:
   - Auto-detected from directory structure
   - Or specify explicitly: `run(base_dir, year, persons=['alice', 'bob'])`

## Running the Pipeline

```python
from src.pipeline import run

results = run('data', 25, persons=['alice', 'bob'])
# Processes data/fy25/alice/ and data/fy25/bob/
# Outputs to data/fy25/{person}/data/
```

