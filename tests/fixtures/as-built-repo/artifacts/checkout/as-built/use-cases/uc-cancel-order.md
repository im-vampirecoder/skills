# Cancel an order

- **Scope:** Checkout
- **Level:** User goal
- **Primary actor:** Signed-in customer
- **Trigger:** The customer asks to cancel one of their orders.

## Preconditions

- The order exists and belongs to the customer. 🟡 OQ2

## Success guarantee

- The order is marked cancelled. ✅ FR3

## Main success scenario

1. The customer asks to cancel the order.
2. The system checks the order is still placed.
3. The system marks the order cancelled.

## Extensions

- 2a. The order is shipped, cancelled or missing: the customer sees ERR3.

## Related requirements

FR3, BR4, ERR3
