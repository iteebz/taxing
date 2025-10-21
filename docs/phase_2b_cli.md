# Phase 2b CLI: Deduction Optimizer

## Overview

The `taxing optimize` command allocates shared deductions across multiple persons to minimize total tax liability. Uses a greedy algorithm: assign deductions to lowest-bracket persons first.

## Setup

### 1. Employment Income Config

Create `employment_income_fy{YEAR}.json` at project root:

```json
{
  "alice": 150000,
  "bob": 50000,
  "charlie": 30000
}
```

### 2. Phase 1 Output

Run Phase 1 pipeline first:

```bash
python -m src.pipeline data 25
```

This generates:
- `data/fy25/alice/data/deductions.csv`
- `data/fy25/bob/data/deductions.csv`
- etc.

## Usage

### Basic Usage

```bash
python taxing optimize --fy 25 --persons alice,bob
```

### With Custom Base Directory

```bash
python taxing optimize --fy 25 --persons alice,bob,charlie --base-dir /path/to/data
```

## Output

```
Person          Employment      Deductions      Bracket  Savings     
---------------------------------------------------------------------------
alice           $150,000        $0              37     % $0          
bob             $50,000         $10,000         30     % $3,000      
charlie         $30,000         $5,000          16     % $800        
---------------------------------------------------------------------------
TOTAL                           $15,000                  $3,800
```

## Algorithm

1. Pool all deductions from each person
2. Sort persons by marginal tax rate (lowest first)
3. Assign deductions up to bracket headroom for each person
4. Continue with next person for remaining deductions

This maximizes tax savings by applying deductions to lower-bracket persons.

## Example: Alice vs Bob

- **Alice**: $150k income → 37% bracket
- **Bob**: $50k income → 30% bracket
- **Shared pool**: $20k deductions

### Greedy Allocation:
1. Bob gets first (30% < 37%)
2. Bob's headroom: $135k - $50k = $85k
3. Bob gets full $20k
4. Tax savings: $20k × 30% = $6k

### Naive Allocation (equal split):
- Each gets $10k
- Tax savings: $10k × 30% + $10k × 37% = $6.7k

**Greedy saves more** by respecting bracket differences.

## Supported Years

Currently: FY25 (Australian tax year 2024-25)

Tax brackets:
- 0-45k: 16%
- 45k-135k: 30%
- 135k-190k: 37%
- 190k+: 45%

## Future Extensions

- Multi-year planning (defer gains to better year)
- Loss carryforward tracking
- Superannuation contribution optimization
