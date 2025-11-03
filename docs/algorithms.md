# core algorithms

## 1. FIFO with loss harvesting + CGT discount

**File**: `src/core/trades.py` → `process_trades(trades: list[Trade]) -> list[Gain]`

### Algorithm (priority-based)

Sort trades by (code, date). For each ticker:

1. Maintain FIFO buffer of buy lots
2. For each sell order:
   - **Priority 1**: Loss lots (buy_price ≥ sell_price)
   - **Priority 2**: Discount-eligible lots (365+ days old)
   - **Priority 3**: FIFO (first in, first out)
3. Calculate profit, apply CGT discount (50% if 365+ days)
4. Emit Gain object

### Example

```
Buys:  BHP @ $10 (Jan 1), BHP @ $15 (Jun 1)
Sell:  BHP @ $12 (Dec 1, 200 units)

FIFO (naive):    Sell 100@$10 (profit $200), 100@$15 (loss $300) = net -$100
Loss harvesting: Sell 100@$15 (loss $300), 100@$10 (profit $200) = net -$100 (same profit, but locks loss first)

Result: Gain(raw_profit=-100, taxable_gain=-100, action="loss")
```

### Partial fill handling

When selling less than a buy lot, use `dataclasses.replace()`:

```python
updated_lot = replace(
    buy_lot,
    units=buy_lot.units - units_to_sell,
    fee=buy_lot.fee - partial_fee, # Assuming fee is Decimal, direct subtraction
)
```

No mutation → full auditability.

### CGT discount logic

```python
if held_days > 365:
    taxable_gain = raw_profit * Decimal("0.5")  # 50% discount
else:
    taxable_gain = raw_profit
```

---

## 2. Tax bracket rate lookup

**File**: `src/core/household.py` → `_tax_rate(income: Decimal, fy: int) -> Decimal`

### AUD FY25 brackets (post Stage 3 cuts)

```
$0-$18,200:           0%
$18,200-$45,000:      16%
$45,000-$135,000:     30%
$135,000-$190,000:    37%
$190,000+:            45%
```

### Algorithm

```python
def _tax_rate(income, fy):
    """Return marginal rate (rate at which last dollar is taxed)."""
    brackets = BRACKETS[fy]  # [(0, 0%), (18200, 19%), ...]
    rate = Decimal("0")
    for threshold, r in brackets:
        if income >= threshold:
            rate = r          # Update as we pass each threshold
    return rate               # Return rate for last bracket we passed
```

### Examples

| Income | Last bracket | Rate |
|--------|--------------|------|
| $10,000 | 0-18200 | 0% |
| $30,000 | 18200-45000 | 19% |
| $60,000 | 45000-120000 | 32.5% |
| $150,000 | 120000-180000 | 37% |

---

## 3. Tax liability calculation (progressive brackets)

**File**: `src/core/household.py` → `_tax_liability(income: Money, fy: int) -> Money`

### Algorithm

```python
def _tax_liability(income: Decimal, fy: int) -> Decimal:
    """Accumulate tax across all brackets up to income level."""
    if income <= 18200:
        return Decimal("0")  # Tax-free threshold
    
    tax = Decimal("0")
    for i, (threshold, rate) in enumerate(brackets):
        if income <= threshold:
            break
        next_threshold = brackets[i+1][0] if i+1 < len(brackets) else income
        taxable_in_bracket = min(income, next_threshold) - threshold
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
    
    return tax
```

### Example: $50,000 income

```
Bracket 1 ($0-$18,200): Taxable = 0 (under threshold), Tax = 0
Bracket 2 ($18,200-$45,000): Taxable = 26,800, Tax = 26,800 * 0.19 = 5,092
Bracket 3 ($45,000-$120,000): Taxable = 5,000, Tax = 5,000 * 0.325 = 1,625

Total tax = $6,717
```

---

## 4. Deduction allocation (threshold + bracket aware)

**File**: `src/core/household.py` → `allocate_deductions(your_income, janice_income, shared_deductions, fy) -> (your_alloc, janice_alloc)`

### Two-phase strategy

**Phase 1: Fill tax-free thresholds**
- You have $0 income → buffer = $18,200 - $0 = $18,200
- Janice has $50,000 income → buffer = $18,200 - $50,000 = $0 (negative, so 0)
- Allocate deductions to fill your threshold first (preserves bracket space, no immediate tax saving but valuable)

**Phase 2: Route excess to lower-bracket person**
- If remaining deductions after phase 1:
  - Your rate: 0% (still in threshold)
  - Janice rate: 32.5% (at $50k income)
  - Route all remaining to you (lower rate)

### Algorithm

```python
def allocate_deductions(your_income, janice_income, shared_deductions, fy):
    threshold = TAX_FREE_THRESHOLD[fy]  # $18,200
    total_ded = sum(shared_deductions)
    
    # Phase 1: Fill thresholds
    your_buf = max(Decimal("0"), threshold - your_income)
    janice_buf = max(Decimal("0"), threshold - janice_income)
    
    your_alloc = min(your_buf, total_ded)
    remain = total_ded - your_alloc
    
    if remain > Decimal("0") and janice_buf > Decimal("0"):
        janice_alloc = min(janice_buf, remain)
        remain -= janice_alloc
    
    # Phase 2: Route by bracket
    if remain > Decimal("0"):
        your_rate = _tax_rate(your_income, fy)
        janice_rate = _tax_rate(janice_income, fy)
        if janice_rate < your_rate:
            janice_alloc = janice_alloc + remain
        else:
            your_alloc = your_alloc + remain
    
    return your_alloc, janice_alloc
```

### Example: Person A $0, Person B $50k, $10k deductions

```
Phase 1:
  A buffer: $18,200 - $0 = $18,200
  B buffer: $18,200 - $50,000 = $0
  Allocate min($18,200, $10,000) = $10,000 to A
  Remaining: $0

Result: A=$10,000, B=$0
(A has full threshold; B is in 32.5% bracket)
```

---

## 5. Household tax optimization

**File**: `src/core/household.py` → `optimize_household(yours, janice) -> Allocation`

### Strategy

1. Compare marginal tax rates
2. If Janice's rate < your rate: consolidate all deductions to Janice (minimize household tax)
3. Otherwise: keep as-is
4. Calculate final tax liability for each person

### Algorithm

```python
def optimize_household(yours, janice):
    your_rate = _tax_rate(yours.income, yours.fy)
    janice_rate = _tax_rate(janice.income, janice.fy)
    
    if janice_rate < your_rate:
        # Consolidate deductions to Janice
        total_ded = sum(yours.deductions) + sum(janice.deductions)
        yours = Individual(
            name=yours.name, fy=yours.fy, income=yours.income,
            deductions=[], gains=yours.gains, losses=yours.losses
        )
        janice = Individual(
            name=janice.name, fy=janice.fy, income=janice.income,
            deductions=[total_ded], gains=janice.gains, losses=janice.losses
        )
    
    your_tax = _tax_liability(yours.taxable_income, yours.fy)
    janice_tax = _tax_liability(janice.taxable_income, janice.fy)
    
    return Allocation(yours, janice, your_tax, janice_tax)
```

---

## 6. Classification (keyword matching)

**File**: `src/core/classify.py` → `classify(description: str, rules: dict) -> set[str]`

### Algorithm

Substring match (case-insensitive). Load rules via `src/core/rules.py` (handles deduplication + subsumed keyword removal).

```python
def classify(description, rules):
    desc_upper = description.strip().upper()
    matches = set()
    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword.upper() in desc_upper:
                matches.add(category)
                break
    return matches
```

### Example
```
Rules: {"groceries": ["COLES", "WOOLIES"], "utilities": ["ELECTRICITY"]}
Description: "COLES SUPERMARKET"
Result: {"groceries"}
```

**Multi-category**: One txn can match multiple categories (e.g., transfer + forex).

---

## 7. Deduction weighting (transaction → deduction)

**File**: `src/core/deduce.py` → `deduce(txns: list[Transaction], fy: int, individual: str, weights_path: Path) -> list[Deduction]`

### Algorithm

For each classified transaction:
1. Look up category weight (from ATO rates or weights.csv)
2. Calculate: deduction = |amount| × weight
3. Emit Deduction object with category, amount, fy, individual

### Example
```
Txn: $100 at Coles, category {"groceries"}, weight=60%
Deduction: Deduction(category="groceries", amount=60, fy=24, individual="janice")
```

Multi-category transactions split proportionally per weight.

---

**Last Updated**: Nov 4, 2025
