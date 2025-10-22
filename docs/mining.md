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
- `--search`: Enable merchant search for categorization hints
- `--show-unlabeled`: Display unclassified txns with search results (manual review mode)

**Output**: Ranked suggestions (keyword → category | evidence | source).

### `tax mine --fy 24 --show-unlabeled --search --limit N`
Manual review mode: Shows unclassified transactions with verbatim search results (title + snippet).

Use this to identify patterns in unlabeled data and decide categories before adding rules.

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

For unclassified txns (via `--show-unlabeled` flag):
1. Search full sanitized description via DDGS
2. Return top 2-3 results verbatim (title + body snippet)
3. Cache results to `.search_cache.json` → no API spam on re-runs
4. Manual categorization: review results, then `tax rules add` to codify decisions

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
