# Known Issues & Refactoring Backlog

## Categorization

### Beem Classification Structure
- **Status**: Open
- **Priority**: Medium
- **Description**: Currently `beems.txt` → `beems` category → `transfers/transfers`. Should align with pattern for other transfer subtypes.
- **Option**: Rename `beems.txt` to `beem.txt` and update cats.yaml to have `beem: {l1: transfers, l2: beem}` for cleaner sub-categorization.
- **Blocker**: Deduplication handling—CBA exports include obfuscated beem txns while Beem export shows same txns. Need to verify dedupe.py correctly handles CBA + Beem overlap before categorizing beem records.

## Data Quality

### Double-Counting Risk (Beem + CBA)
- **Status**: Open
- **Priority**: High
- **Description**: Beem transactions appear in both CBA export (obfuscated as "beem it") and Beem export (verbatim). Dedupe.py handles beemit P2P (both sides), but unclear if CBA + Beem export overlap is deduplicated.
- **Action**: Audit dedupe.py logic for CBA/Beem cross-export deduplication before categorizing beem records.

