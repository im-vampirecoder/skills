---
id: FEATURE-card-wallet
status: draft
---

# Feature PRD: Card wallet

## Touchpoints
- Payment page

## Requirements

### Functional
- **FR-card-wallet.show-receipt** (P1): When a saved card payment succeeds, the system shall show the receipt.

### Non-functional
- **NFR-card-wallet.payment-response-time:** The customer sees the payment result within 5 s at peak.

### Business rules
- **BR-card-wallet.max-retry-per-card:** A saved card can be tried at most 5 times in 10 minutes. Applies to FR-card-wallet.show-receipt.

## Decisions
- [2026-10-16] not a conflict: FR-checkout.show-receipt vs FR-card-wallet.show-receipt — why: different flows — by: PO
