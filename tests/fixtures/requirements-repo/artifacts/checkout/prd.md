---
id: FEATURE-checkout
epic_id: null
ado_id: null
last_synced: null
status: draft
---

# Feature PRD: Checkout

## Overview
Customers pay for the order in their cart.

## Requirements

### Functional
- **FR-checkout.pay-with-stripe** (P0): When the customer confirms the order, the system shall charge the card through Stripe.
- **FR-checkout.guest-pay** (P1): When a guest confirms the order, the system shall take payment without an account.
- **FR-checkout.show-receipt** (P0): When payment succeeds, the system shall show the order receipt. [NEEDS CLARIFICATION: email copy too?]

### Non-functional
- **NFR-checkout.payment-response-time:** The customer sees the payment result within 3 s at peak (500 orders/hour).

### Business rules
- **BR-checkout.max-retry-per-card:** A card can be tried at most 3 times in 10 minutes. Applies to FR-checkout.pay-with-stripe.

### Errors
| ID | If | The user sees | For |
|---|---|---|---|
| ERR-checkout.card-declined | the bank declines the card | "Your card was declined." | FR-checkout.pay-with-stripe |

## Open Questions
- Do we keep failed orders?

## Decisions
- [2026-10-15] Stripe only at launch — options: Stripe / Adyen — why: existing contract — by: PO
