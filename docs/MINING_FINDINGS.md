# Mining Session Findings & Recommendations

**Date**: 2025-10-25  
**Coverage**: 81.8% → 84.2% (added 14 rules)  
**Status**: Too-generic rules detected, halting to propose taxonomy

## Problem Identified

Rules being added are increasingly **generic**, causing false positives and poor categorization:
- `store` → supermarket (matches "bookstore", "hardware store", "app store")
- `food` → dining (matches "fast food", "dog food", "food delivery")
- `deposit` → transfers (matches "deposit" in descriptions, not just bank transfers)
- `shi`, `don`, `east` → dining (substring matches, wildly overfit)

**Root Cause**: Flat category structure (50 categories) lacks hierarchy. No distinction between:
- Primary categories (dining vs. groceries vs. supermarket) — functionally different
- Deduction-relevant buckets (home_office: electricity, gas, internet, rent) vs. personal spending

## Current Category Structure

### 50 Flat Categories
```
accessories, accom, bars, beems, bnpl, books, business, car, clothing, 
convenience, cosmetics, craft, debts, dining, donations, electronics, 
entertainment, events, fees, food_delivery, gifts, groceries, hobbies, 
home_office, home_stores, income, internet, investment, liquor, medical, 
mobile, mobile_accessories, nicotine, online_retail, pet, property, 
refunds, rent, scam, self_care, self_education, software, sports, 
subscriptions, supermarket, taxation, taxi, therapy, transfers, transport, 
travel, trust, utilities, work_accessories
```

### Deduction Groups (from config.yaml)
Only 4 actual deduction categories are configured:
1. **home_office**: electricity, gas, internet, rent
2. **vehicle**: fuel, insurance, registration, maintenance
3. **meals**: fixed rate (50%)
4. **donations**: fixed rate (100%)

### Tax Treatment Patterns
- **Deductible** (business use): home_office, vehicle, meals, donations, medical, education
- **Non-deductible**: dining, groceries, entertainment, hobbies, nicotine, cosmetics, clothing
- **Pass-through** (transfers, not expense): transfers, trust, income, refunds
- **Income proxies** (track for deduction calc): business, self_education, work_accessories

## Proposed 2-Level Taxonomy

### Tier 1: Deduction Groups (7 main buckets)
Maps to actual tax treatment, not merchant type:

```
WORK_EXPENSES (sub_to_main_cat: business → vehicle → home_office)
├── home_office: electricity, gas, internet, rent, work_accessories
├── vehicle: fuel, car, taxi, transport, registration, maintenance
├── business: business (consulting, side hustle)
└── education: self_education, books

HEALTH (actual_cost_categories eligible)
├── medical: medical, therapy, pharmacy
└── health_and_fitness: sports, self_care (lower priority)

HOUSEHOLD (actual_cost_categories eligible)
├── utilities: electricity, gas, internet, utilities
├── rent_housing: rent, property, home_stores, home_office (overlap with work)
└── household: groceries, supermarket, convenience, pet

DISCRETIONARY (fixed-rate or non-deductible)
├── dining: dining, bars, food_delivery
├── entertainment: entertainment, events, hobbies, nightlife
├── personal: clothing, accessories, cosmetics, nicotine, gifts
└── subscriptions: software, subscriptions, internet (overlap with work)

INCOME (tracking, not expenses)
├── income_employment: salary deposits
├── income_investment: investment returns
└── income_business: business income

TRANSFERS (non-expenses)
├── transfers: internal transfers, P2P
├── trust: family transfers, trusts
└── debt_repayment: bnpl, debts

OTHER
├── fees: bank fees, taxation, scam
├── donations: donations (fixed 100%)
```

### Mapping Strategy

**Step 1**: Refactor deduce.py to use `sub_to_main_cat` from Tier 1  
**Step 2**: Rules stay flat (1 level) but mining becomes tier-aware  
**Step 3**: Create `src/core/cats.py` with:
  - Deduction group definitions
  - Tier-1 → Tier-2 mapping
  - Tax treatment metadata (deductible%, fixed_rate, etc.)

## Mining Strategy Refinement

**Problem with current approach**:
- Mining on 50 flat categories → generic keywords bubble up
- High-dominance keywords are often category names, not merchants

**Better approach**:
1. Mine at Tier 2 level (dining → split, don, shi, etc.)
2. Flag suggestions only when evidence > threshold in that specific sub-category
3. Review cross-category collisions (e.g., "internet" appears in both utilities + subscriptions)
4. Add rules cautiously: require ~5+ occurrences in same merchant or pattern, not just keyword presence

## Rules Added This Session (Problematic)

❌ Too generic (revert before next run):
- `deposit` → transfers (catches invoice deposits, bank deposits, security deposits)
- `store` → supermarket (false positives: app store, bookstore, hardware store)
- `food` → dining (false positives: fast food, dog food, food delivery)
- `shi`, `don`, `east` → dining (substrings, overfitting)

✅ Good (keep):
- `mondo` → dining (merchant name, specific)
- `fantuan`, `little turtle` → dining (merchant name, specific)
- `park` → car (parking, consistent)
- `apple` → software (Apple subscriptions/apps)
- `booking` → accom (Booking.com is specific)
- `payid` → travel (PayID transactions typically travel/flight bookings)

## Next Hailot TODO

1. **Create `src/core/cats.py`**:
   - Define `Tier1` and `Tier2` enums or dicts
   - Map Tier 2 → deduction treatment
   - Sub-category mapping for rules.py

2. **Refactor deduce.py**:
   - Use cats.py for sub_to_main_cat
   - Simplify actual_cost_categories logic

3. **Mining improvements**:
   - Add `--tier` flag to mine at Tier 2
   - Flag cross-category collisions (e.g., "internet" in 2+ categories)
   - Add confidence scoring for rules (not just evidence count)

4. **Rule cleanup**:
   - Audit existing rules for false positives
   - Remove 1-2 letter keywords (shi, don, lin, sal, dad, bad, nan)
   - Require merchant names ≥ 4 chars or patterns (e.g., city names only for dining if high dominance)

5. **Documentation**:
   - Update mining.md with taxonomy rationale
   - Add examples of good vs. bad rules
