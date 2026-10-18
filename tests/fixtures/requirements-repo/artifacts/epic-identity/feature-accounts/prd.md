---
id: FEATURE-accounts
epic_id: EPIC-identity
status: delivered
delivered: 2026-09-30
---

# Feature PRD: Accounts

## Requirements

### Functional
- **FR-accounts.sign-in-with-email** (P0, FR3): When the customer submits email and password, the system shall sign them in.
> Clarified on 2026-10-05: email match is case-insensitive — BUG-login-case
- **FR-accounts.old-sign-in** (P0): Retired. Replaced by FR-accounts.sign-in-with-email.

### Business rules
- **BR-accounts.login-before-purchase:** A customer must be signed in to buy. Applies to FR-accounts.sign-in-with-email.
