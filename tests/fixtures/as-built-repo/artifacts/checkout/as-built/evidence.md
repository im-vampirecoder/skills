# Checkout - evidence

## Entry points

| Entry point | Kind | Source |
|---|---|---|
| POST api/orders | HTTP endpoint, signed-in only | `src/shop-api/Controllers/OrdersController.cs:18` |
| GET api/orders/{id} | HTTP endpoint, signed-in only | `src/shop-api/Controllers/OrdersController.cs:31` |
| POST api/orders/{id}/cancel | HTTP endpoint, signed-in only | `src/shop-api/Controllers/OrdersController.cs:38` |
| POST api/orders/legacy | HTTP endpoint, obsolete | `src/shop-api/Controllers/OrdersController.cs:52-54` |
| CheckoutScreen | Mobile screen | `src/shop-app/src/screens/CheckoutScreen.tsx:6` |

## Validation

| Field | Rule | Source |
|---|---|---|
| Items | Not empty | `src/shop-api/Validators/PlaceOrderValidator.cs:9` |
| Items[].Quantity | 1 to 99 | `src/shop-api/Validators/PlaceOrderValidator.cs:12` |
| DeliveryPostcode | Required, 4 to 10 characters | `src/shop-api/Validators/PlaceOrderValidator.cs:14` |

## Errors

| Code or key | Wording | Throw site | Catalog |
|---|---|---|---|
| orders.empty_cart | "Your cart is empty. Add at least one item to place an order." | `src/shop-api/Validators/PlaceOrderValidator.cs:9` | `src/shop-api/Resources/Messages.resx:4` |
| orders.too_many_items | "An order can hold at most 20 items." | `src/shop-api/Controllers/OrdersController.cs:23` | `src/shop-api/Resources/Messages.resx:7` |
| orders.cannot_cancel | "This order can no longer be cancelled." | `src/shop-api/Controllers/OrdersController.cs:44` | `src/shop-api/Resources/Messages.resx:10` |
| orders.not_found | unresolved | `src/shop-api/Controllers/OrdersController.cs:35` | not found |

## Rules and constants

| Rule | Value | Source |
|---|---|---|
| MaxItemsPerOrder | 20 | `src/shop-api/Controllers/OrdersController.cs:13` |
| Cancel only when status is Placed | OrderStatus.Placed | `src/shop-api/Controllers/OrdersController.cs:42` |
| Item limit has an active test | 21 items rejected | `src/shop-api/tests/OrdersControllerTests.cs:8-13` |

## Entities

| Entity | Stored as | Source |
|---|---|---|
| Order | Order class with OrderStatus enum | `src/shop-api/Domain/Order.cs:10-23` |
| OrderItem | Record | `src/shop-api/Domain/Order.cs:25` |

## Cross-repo hops

| From | To | Through | Source (from) | Source (to) |
|---|---|---|---|---|
| Checkout screen places an order | Order endpoint | HTTP POST to the orders path | `src/shop-app/src/screens/CheckoutScreen.tsx:10` | `src/shop-api/Controllers/OrdersController.cs:18` |

## Gaps

| Gap | Search run | Scope |
|---|---|---|
| Ship action has no caller | `grep -rn "Ship()" src/` | shop-api, shop-app |
| Legacy endpoint has no caller | `grep -rn "orders/legacy" src/shop-app` | shop-app |
