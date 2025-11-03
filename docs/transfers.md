# Transfer Categorization Strategy

## Current State
All transfers lumped into `transfers/transfers`.

## Proposed: Transfer Sub-taxonomy

### transfers/self
Moving money between own accounts (e.g., tyson's offset → savings).

**Implementation**: Trivial. Auto-detect: `from_person == to_person`.

### transfers/household
Transfers within household (e.g., tyson ↔ janice).

**Implementation**: Config-based. Define household members in a config file, auto-detect when both sides are known members.

### transfers/family
Transfers to/from family members.

**Implementation**: Rule file pattern (e.g., `transfer to zhou v`, `transfer from mum`). Use existing rule infrastructure.

### transfers/friends
Transfers to/from friends.

**Implementation**: Rule file pattern. Similar to family.

### transfers/loan
Loan-related transfers (drawdowns, repayments).

**Implementation**: Pattern matching in description. Rules already exist: `proceeds of loan drawdown`, `reversal of debit entry`, etc.

## Tax Relevance
- **Self/household**: Noise at household level (move money around, not income/deduction).
- **Family/friends**: Potentially taxable (gift vs loan intent unclear from transaction alone).
- **Loan**: Loan repayment is not income; drawdown is not expense. Different tax treatment.

## Implementation Roadmap
1. **Phase 1** (now): Keep all as `transfers/transfers`. Document intent gaps.
2. **Phase 2** (post-98% coverage): Implement transfers/self + transfers/household (auto-detect).
3. **Phase 3** (optional): Add rule files for transfers/family, transfers/friends, transfers/loan.
4. **Phase 4** (audit): Post-pipeline manual review of external transfers >threshold for intent verification.

## Known Challenges
- **Intent ambiguity**: Transaction alone doesn't tell if family transfer is gift or loan.
- **Rule maintenance**: Growing rule files for family/friend patterns (personal to each household).
- **Edge cases**: Joint accounts, trusts, business transfers (separate from personal).

