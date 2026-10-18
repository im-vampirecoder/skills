---
feature_id: FEATURE-checkout
status: draft
---

# Checkout

## Requirements

### Functional
- **FR-checkout.review-cart** (P0): When the customer opens the cart, the system shall show each item, its quantity and the order total.
- **FR-checkout.pay-with-card** (P0): When the customer confirms the order, the system shall charge the card.
- **FR-checkout.save-card** (P2): When the customer ticks "save card", the system shall keep the card for next time.
- **FR-checkout.pay-with-stripe** (P1): When the customer confirms the order, the system shall charge the card through Stripe. Retired. Replaced by FR-checkout.pay-with-card.

### Business rules
- **BR-checkout.retry-limit:** A card can be tried at most 3 times in 10 minutes. Applies to FR-checkout.pay-with-card.

### Errors

| ID | If | The user sees | FR |
|---|---|---|---|
| ERR-checkout.card-declined | the bank declines the card | "Your card was declined. Try another card." | FR-checkout.pay-with-card |
| ERR-checkout.too-many-tries | the retry limit is reached | "Too many attempts. Try again in 10 minutes." | FR-checkout.pay-with-card |
| ERR-checkout.audit-write-failed | the audit log write fails | — | FR-checkout.pay-with-card |
