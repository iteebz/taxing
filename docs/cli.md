# taxing CLI & Pipeline Operations

## Quick Start

```bash
# Run full pipeline: ingest → classify → deduce → trades → persist
python -m src.cli run --fy 24 --base-dir .

# View coverage & household metrics (from classified data)
python -m src.cli metrics --fy 24 --base-dir .

# All available commands
python -m src.cli --help
```

## Mental Model

### Data Flow

```
raw/
├── anz.csv          ──┐
├── cba.csv          ──┼──→ ingest_year() ──→ dedupe() ──→ classify() ──→ deduce()
├── beem.csv         ──┤                                        ↓
├── wise.csv         ──┤                                    to_csv()
└── trades.csv       ──┘                                        ↓
                                                            data/
                                                            ├── transactions.csv
                                                            ├── deductions.csv
                                                            ├── summary.csv
                                                            └── gains.csv
```

### Key Concepts

1. **Beem Username Inference**: Automatically detected from payer/recipient frequency in beem.csv
   - No config needed - inferred at ingestion time
   - `_infer_beem_user()` in `src/io/ingest.py`

2. **NaN Handling**: Wise NEUTRAL transactions (currency conversions) may produce NaN
   - Filtered at metrics/pipeline level: `is_nan()` check
   - Safe to ignore (0 impact on tax calculation)

3. **Transaction Classifications**: Happen in-memory during pipeline
   - Rules loaded from `rules/*.txt` 
   - 54 categories available
   - Output: classified_count metric

4. **Persistence**: Pipeline writes 4 CSVs per person per year
   - `transactions.csv` - classified, with category field
   - `deductions.csv` - calculated deductible amounts
   - `summary.csv` - category aggregates (credit/debit)
   - `gains.csv` - capital gains

## Commands

### run
```bash
python -m src.cli run --fy 24 --base-dir .
```
Executes complete pipeline for a fiscal year. Outputs:
- Transaction counts
- Classification counts
- Deduction counts
- Capital gains counts

**Note**: Pipeline automatically writes classified data to `data/fy{year}/{person}/data/*.csv`

### metrics
```bash
python -m src.cli metrics --fy 24 --base-dir .
python -m src.cli metrics --fy 24 --person janice --base-dir .
```
Calculates coverage & household metrics from raw transactions.

**Note**: Currently reads raw transactions (not classified). For classified metrics, read the output CSVs from pipeline.

### gains-plan
```bash
python -m src.cli gains-plan --projection 25:30%,26:45% --gains 50000,30000 --losses 10000
```
Multi-year capital gains planning with bracket projection.

### optimize
```bash
python -m src.cli optimize --fy 25 --persons alice,bob
```
Allocate deductions across household to minimize tax.

### property
```bash
python -m src.cli property --fy 25 --person alice
```
Aggregate property expenses.

### rule
```bash
tax rule groceries "WOOLWORTHS"
```
Adds a new classification rule. This command takes the category name and keyword as positional arguments.

**Note**: This is a streamlined version of the old `tax rules add --category CATEGORY --keyword KEYWORD` command.

### rules
```bash
tax rules suggest --fy 24
tax rules test --category dining --keyword CAFE
tax rules clean
```
Manages classification rules for mining, testing, and cleaning.

- `suggest`: Mine high-confidence rule suggestions.
- `test`: Test a rule against classified transactions before adding.
- `clean`: Remove duplicates, strip comments, and sort alphabetically in rule files.

## Architecture

### Pipeline (`src/pipeline.py`)

The `run(base_dir, year, persons=None)` function orchestrates:

1. **Ingest**: Load CSVs from `data/fy{year}/{person}/raw/*.csv`
   - Handles ANZ, CBA, Beem, Wise multi-bank formats
   - Auto-infers Beem username from data

2. **Dedupe**: Remove duplicates via cross-ledger fingerprinting
   - Same transaction appearing in multiple bank feeds

3. **Classify**: Apply rules to categorize transactions
   - Uses `classify()` from `src/core/classify.py`
   - 54 categories from `rules/*.txt`

4. **Validate**: Check for data quality issues
   - `validate_transactions()` from `src/core/validate.py`

5. **Deduce**: Calculate deductions based on category & weights
   - Uses `deduce()` from `src/core/deduce.py`

6. **Trades**: Process capital gains
   - `ingest_trades_year()` loads trades
   - `process_trades()` calculates FIFO gains with CGT discount

7. **Persist**: Write classified data to CSVs
   - `to_csv()` from `src/io/persist.py`

### Key Files

| File | Purpose |
|------|---------|
| `src/pipeline.py` | Orchestrates ingest→classify→deduce→trades→persist |
| `src/io/ingest.py` | CSV loading with bank-specific converters |
| `src/io/converters.py` | ANZ, CBA, Beem, Wise format parsers |
| `src/core/classify.py` | Rule-based transaction categorization |
| `src/core/deduce.py` | Calculate deductions from categories |
| `src/core/trades.py` | FIFO + CGT discount calculations |
| `src/core/metrics.py` | Coverage & household metrics |
| `src/cli/commands/run.py` | CLI entry point for pipeline |

## Validation Strategy

### Step 1: Run taxing/ on FY23-24
```bash
python -m src.cli run --fy 23 --base-dir .
python -m src.cli run --fy 24 --base-dir .
```

Check output: 
- FY23: janice 360/391 classified, tyson 370/596 classified
- FY24: janice 725/1219 classified, tyson 364/461 classified

### Step 2: Compare with tax-og/
1. Extract same FY23-24 data to tax-og/ directory structure
2. Run tax-og/ pipeline
3. Compare deduction totals, category summaries

### Step 3: Validate Parity
- Same classification rules → same category assignments
- Same deduction logic → same dollar amounts
- Any differences → investigate rule/weight changes

## Troubleshooting

### Pipeline fails with "beem_username required"
**Old issue** - now auto-inferred. Should not occur.

### Wise transactions show NaN
Expected for NEUTRAL/cancelled directions. Filtered at metrics level. No impact on tax calculations.

### No transactions classified
Check `rules/*.txt` files exist and have correct format.

### Command not found
Ensure you're running from `/Users/teebz/space/taxing` directory with `python -m src.cli`.

## Testing

```bash
just test              # Run all tests
just test -k wise     # Run Wise-specific tests
just cov              # Coverage report
python -m pytest tests/integration/test_pipeline.py -v  # Full pipeline test
```

Expected: 209 tests passing, all coverage metrics green.

## Design Decisions

### Why infer Beem username?
Config files are error-prone. Beem CSVs contain the username - detect from frequency.

### Why filter NaN at metrics/pipeline?
Wise NEUTRAL transactions don't represent actual money movement. Filtering preserves data integrity without losing meaningful calculations.

### Why separate CLI commands?
Each command is independent and testable. `run` orchestrates full pipeline; others are specialized operations.

### Why write CSVs?
Immutable audit trail. Pipeline outputs are reference-grade and reproducible.
