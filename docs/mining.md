# rule mining protocol

**Goal**: Maximize coverage (→90%+) via keyword mining + merchant search.

## quick start

```bash
# 1. Check coverage gaps
tax coverage --fy 24 --sample 10

# 2. Mine rule suggestions (keyword-based)
tax mine --fy 24 --threshold 10 --limit 20

# 3. Add high-confidence rules
tax rules add --category dining --keyword CAFE
tax rules add --category groceries --keyword COLES

# 4. Re-run pipeline
tax run --fy 24

# 5. Check new coverage
tax coverage --fy 24
```

## commands

### `tax coverage --fy 24 [--sample N]`
Shows coverage metrics + N random uncategorized txns to investigate.

**Output**: % txns categorized, % spending categorized, % income categorized, sample txns.

### `tax mine --fy 24 [--threshold 10] [--dominance 0.6] [--limit 20]`
Mines rule suggestions from labeled txns. Shows keyword → category mappings with evidence.

**Options**:
- `--threshold N`: Min evidence required (default: 10)
- `--dominance F`: Category dominance threshold 0.0-1.0 (default: 0.6)
- `--limit N`: Max suggestions to show (default: 20)
- `--search`: Enable merchant DDGS search for orphans (slower, higher recall)

**Output**: Ranked suggestions (keyword → category | evidence | source).

### `tax run --fy 24`
Re-runs pipeline with current rules.

### `tax metrics --fy 24`
Household metrics (spending, income, transfers by person).

---

## workflow

1. **Scout**: `tax coverage --fy 24 --sample 20` → see what's unclassified
2. **Mine**: `tax mine --fy 24` → get keyword suggestions ranked by evidence
3. **Review**: Pick high-evidence suggestions (evidence ≥10 with 60% dominance)
4. **Add**: `tax rules add --category X --keyword Y` for each rule
5. **Validate**: `tax run --fy 24` → `tax coverage --fy 24` → check improvement
6. **Iterate**: Repeat until coverage ≥90%

---

## mechanics

### Keyword Mining (`src/core/mining.py`)

For each unlabeled txn:
1. Extract keywords from description (alphanumeric, ≥3 chars)
2. Find labeled txns with keyword overlap
3. Count evidence per (keyword, category) pair
4. Score by threshold + dominance

**Threshold**: Keyword must appear in ≥N labeled txns.
**Dominance**: If keyword maps to multiple categories, pick dominant (>D% of evidence).

Example:
- "COFFEE" in 70 dining + 30 grocery txns → dining wins (70% > 60% dominance)
- Evidence=100 → passes threshold=10

### Search Enhancement (`src/lib/search.py`)

For unlabeled txns with no keyword match (orphans):
1. Search merchant name via DDGS (3 results)
2. Extract category hints from snippets (dining, accom, travel, supermarket, software, medical, electronics, online_retail)
3. Cache results → no API spam on re-runs
4. Emit suggestions with source="search"

---

## config tuning

**Default**: `--threshold 10 --dominance 0.6`

**Loose** (high recall, more false positives): `--threshold 2 --dominance 0.5`
**Tight** (high precision, fewer rules): `--threshold 20 --dominance 0.7`

---

## anti-patterns

❌ Add rules blindly without reviewing context
❌ Trust merchant search alone (can match wrong category)
❌ Ignore GENERIC_WORDS filter (transfer, bank, payment auto-filtered)

✅ Start conservative, tighten if false positives appear
✅ Review each rule before adding
✅ Use `--search` for stubborn orphans only
