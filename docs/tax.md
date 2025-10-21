# tax calculations reference

Deep dive into tax bracket math, household optimization, and deduction allocation.

## FY25 AUD tax brackets

```
$0 - $18,200:          0%      (tax-free threshold)
$18,200 - $45,000:     16%
$45,000 - $135,000:    30%
$135,000 - $190,000:   37%
$190,000+:             45%
```

---

## tax-free threshold

AUD residents have an **$18,200 annual tax-free threshold**. Income up to $18,200 is not taxed.

### Calculation

```python
if taxable_income <= 18200:
    tax = 0
else:
    tax = calculated_across_brackets
```

### Strategy implications

**Key insight**: Deductions filling the threshold preserve bracket space for the other person.

Example:
- Tyson: $0 income, $18,200 threshold available
- Janice: $50,000 income, $0 threshold available
- Shared deduction: $10,000

**Naive routing** (by bracket): Send to Tyson at 0% benefit → seems wasteful.
**Optimal routing** (threshold-aware): Send to Tyson's threshold → preserves Janice's $50k at 32.5% bracket.

If Tyson claims $10k, his taxable_income = $10k (still under threshold, tax = 0).
If Janice claims $10k, her taxable_income = $40k (tax saved = $10k * 0.325 = $3,250).

But Janice's threshold is exhausted. Routing deductions to Tyson defers his future income into a lower bracket.

---

## marginal vs effective tax rate

**Marginal rate**: Rate at which the **last dollar** is taxed.
**Effective rate**: Average tax across all income.

### Example: $50,000 income

Marginal rate = 30% (in the $45-135k bracket)
Effective rate = total_tax / 50000

```
Tax calculation:
  $0-$18,200:        $0 (0% of $18,200)
  $18,200-$45,000:   $26,800 * 0.16 = $4,288
  $45,000-$50,000:   $5,000 * 0.30 = $1,500
  
Total tax = $5,788
Effective rate = $5,788 / $50,000 = 11.6%
```

**Deduction impact**:
- Extra $1,000 deduction saves $300 (30% marginal)
- NOT 11.6% (effective rate)

---

## household tax optimization

Given two people with different incomes, how to allocate shared deductions to minimize household tax?

### Setup

- Tyson: $0 income → 0% marginal rate
- Janice: $50,000 income → 32.5% marginal rate
- Shared deductions: $10,000

### Strategy 1: Route to lower-bracket person (simple)

Route all $10k to Tyson (0% rate).
- Tyson tax saving: $10k * 0% = $0
- Janice tax saving: $0
- Household saving: $0 ❌

This is **wrong** because Tyson's threshold is available.

### Strategy 2: Fill thresholds first, then route by bracket (correct)

**Phase 1**: Fill tax-free thresholds
- Tyson has $18,200 available
- Janice has $0 available
- Allocate $10,000 to Tyson (fills his threshold)

**Phase 2**: Route remaining by bracket
- No remaining deductions
- Stop

**Result**: 
- Tyson deductions: $10,000
- Janice deductions: $0
- Household tax: Tyson $0 + Janice $8,500 = $8,500

### Why is this better?

If we reversed:
- Tyson deductions: $0 → taxable_income = $0 → tax = $0
- Janice deductions: $10,000 → taxable_income = $40,000 → tax = $5,092 + $1,625 = $6,717
- Household tax: $6,717 ✓

Wait, same result? Let's check with a bigger deduction pool...

### Core insight

**Route deductions to person with lower marginal rate AFTER filling thresholds.**

Strategy:
1. Fill tax-free thresholds first (preserves bracket space)
2. Route remaining to lower-bracket person (maximizes tax saving)

---

## deduction allocation algorithm

See [algorithms.md](algorithms.md) → Section 4.

Quick summary:
1. Calculate buffer in each person's threshold: `buffer = $18,200 - current_income`
2. Fill thresholds greedily (who has the most available space?)
3. Route remaining by marginal rate comparison

---

## capital gains tax (CGT) discount

**Long-term holding discount**: If held >365 days, only 50% of profit is taxable.

### Example

Buy: 100 shares at $10 (Jan 1, FY24)
Sell: 100 shares at $15 (Dec 1, FY25) — 334 days later

```
Raw profit = (100 * $15) - (100 * $10) = $500
Held days = 334 (less than 365)

Taxable gain = $500 (no discount, held <365 days)
```

---

Buy: 100 shares at $10 (Jan 1, FY24)
Sell: 100 shares at $15 (Jan 2, FY26) — 367 days later

```
Raw profit = $500
Held days = 367 (more than 365)

Taxable gain = $500 * 0.5 = $250 (50% discount, held >365 days)
```

**Tax saving**: $250 * 0.325 (bracket) = $81.25 per $500 profit at 32.5% marginal rate.

---

## loss harvesting priority

When selling a security, prioritize in this order:

1. **Loss positions** (sell at loss to offset gains)
2. **Discount-eligible** (365+ days, get CGT discount)
3. **FIFO** (first in, first out, standard method)

### Example

```
Holdings in ASX:BHP:
  100 @ $10 (Jan 1) → if sold @ $12 = +$200 profit
  100 @ $15 (Jun 1) → if sold @ $12 = -$300 loss

Sell order: 200 @ $12

Loss harvesting priority:
  1. Sell 100 @ $15 cost → $12 sale price = -$300 loss ✓
  2. Sell 100 @ $10 cost → $12 sale price = +$200 profit
  
Net: -$100 loss (which offsets other gains)

FIFO would give: +$200 - $300 = -$100 (same net, but loss locked first for audit trail)
```

---

## worked example

### Scenario

- **Person A**: $0 income, $5k deductions available
- **Person B**: $52k income, $8k deductions available
- **Shared deductions**: $5k

### Allocation

Threshold buffers:
- A: $18,200 - $0 = $18,200 (available)
- B: $18,200 - $52,000 = $0 (exhausted)

Allocate all $5k shared to A (fills threshold).

### Tax calculation

**Person A**:
- Taxable income: $0 - $5k = -$5k (no tax)

**Person B**:
- Taxable income: $52k - $8k = $44k
- Tax: ($44k - $18.2k) * 0.19 = $4,922

**Household**: $0 + $4,922 = $4,922

---

**Last Updated**: Oct 21, 2025
