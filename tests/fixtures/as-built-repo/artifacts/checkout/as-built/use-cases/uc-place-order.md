# Place an order

- **Scope:** Checkout
- **Level:** User goal
- **Primary actor:** Signed-in customer
- **Trigger:** The customer taps Place order on the checkout screen.

## Preconditions

- The customer is signed in. ✅ S1:10

## Success guarantee

- The order is saved as placed and the confirmation is shown. ✅ FR1

## Main success scenario

1. The customer reviews the order on the checkout screen.
2. The customer taps Place order.
3. The system checks the cart and saves the order as placed.
4. The app shows the order confirmation.

## Extensions

- 3a. The cart is empty: the app shows ERR1.
- 3b. The cart holds more than 20 items: the app shows ERR2.

## Related requirements

FR1, BR1, BR2, BR3, ERR1, ERR2
