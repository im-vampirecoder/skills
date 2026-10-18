---
feature_id: FEATURE-checkout
status: as-built
generated_at: 2026-10-18
sources: [shop-api@0000000, shop-app@0000000]
asserted: 22
corroborated: 1
inferred: 4
open_questions: 3
---

# Checkout - as built

## Confidence legend

| Label | Meaning |
|---|---|
| ✅ | Stated by the code or by an active test at the cited line |
| 🔵 | Inferred, backed by two or more independent places in the code |
| 🟡 | Inferred; the code doesn't say. Needs confirmation |

## Scope

| Statement | Label | Source |
|---|---|---|
| A signed-in customer reviews their cart and places an order from the mobile app. | ✅ | S5:9-15, S1:18-29 |
| A customer can cancel an order that hasn't shipped yet. | ✅ | S1:38-50 |
| The feature exists so customers can buy without contacting the shop. | 🟡 | - |

## Actors

| Actor | Can do | Label | Source |
|---|---|---|---|
| Signed-in customer | Place an order, view it, cancel it while it is still placed | ✅ | S1:10, S1:26 |
| Shop staff | Mark an order as shipped | 🟡 | S4:20 |

## Functional

| ID | When | The system | Label | Source |
|---|---|---|---|---|
| FR1 | A customer places an order with a valid cart | Saves the order as placed and shows the order confirmation | ✅ | S1:26-28, S5:12 |
| FR2 | A customer opens one of their orders | Shows the order, or a not-found message when it doesn't exist | ✅ | S1:31-36 |
| FR3 | A customer cancels a placed order | Marks the order as cancelled | ✅ | S1:38-50, S4:22 |

## Non-functional

_Omitted: the code states no performance, availability or security target for this feature._

## Business rules

| ID | Rule | Applies to | Label | Source |
|---|---|---|---|---|
| BR1 | An order holds at most 20 items. | FR1 | ✅ | S1:13, S1:21, S6:9 |
| BR2 | Each item's quantity is between 1 and 99. | FR1 | ✅ | S2:12 |
| BR3 | A delivery postcode of 4 to 10 characters is required. | FR1 | ✅ | S2:14 |
| BR4 | Only an order that is still placed (not shipped or cancelled) can be cancelled. | FR3 | ✅ | S1:42 |
| BR5 | The 20-item limit exists to keep orders within one delivery. | FR1 | 🟡 | - |

## Errors

| ID | If | The user sees | For | Label | Source |
|---|---|---|---|---|---|
| ERR1 | The cart is empty | "Your cart is empty. Add at least one item to place an order." | FR1 | ✅ | S2:9, S3:4 |
| ERR2 | The cart holds more than 20 items | "An order can hold at most 20 items." | FR1 | ✅ | S1:23, S3:7 |
| ERR3 | The order is already shipped or cancelled | "This order can no longer be cancelled." | FR3 | ✅ | S1:44, S3:10 |
| ERR4 | The order doesn't exist | key `orders.not_found` (unresolved) | FR2 | 🟡 | S1:35 |

## State transitions

| Entity | From | To | Trigger | Label | Source |
|---|---|---|---|---|---|
| Order | (new) | Placed | Customer places the order | ✅ | S4:15 |
| Order | Placed | Cancelled | Customer cancels | ✅ | S4:22, S1:47 |
| Order | Placed | Shipped | Order is dispatched | 🔵 | S4:20, S4:6 |

## Success criteria

| Statement | Label | Source |
|---|---|---|
| A placed order can be opened again by the customer who placed it. | ✅ | S1:28, S1:31-36 |

## Entities

| Entity | Holds | Label | Source |
|---|---|---|---|
| Order | Customer, items, status | ✅ | S4:10-23 |
| Order item | Product and quantity | ✅ | S4:25 |

Details: [erd.md](erd.md).

## Flows

| Flow | Summary | Label | Source |
|---|---|---|---|
| place-order | Customer reviews the cart and places an order | ✅ | S5:9-15, S1:18-29 |
| cancel-order | Customer cancels a placed order | ✅ | S1:38-50 |

Details: [flows.md](flows.md).

## Screens

| Screen | Purpose | Label | Source |
|---|---|---|---|
| Checkout | Review the order and place it; shows the error message on failure | ✅ | S5:18-24 |

## Constraints & dependencies

| Statement | Label | Source |
|---|---|---|
| Every order action requires a signed-in customer. | ✅ | S1:10 |

## Sources

| ID | Path | Lines | What it covers |
|---|---|---|---|
| S1 | src/shop-api/Controllers/OrdersController.cs | 9-55 | Order endpoints, limits, errors |
| S2 | src/shop-api/Validators/PlaceOrderValidator.cs | 9-14 | Order validation |
| S3 | src/shop-api/Resources/Messages.resx | 3-11 | Error wording |
| S4 | src/shop-api/Domain/Order.cs | 3-25 | Order and its statuses |
| S5 | src/shop-app/src/screens/CheckoutScreen.tsx | 6-25 | Checkout screen |
| S6 | src/shop-api/tests/OrdersControllerTests.cs | 8-13 | Item limit test |

## Open questions

| ID | Question | About | Why the code can't answer |
|---|---|---|---|
| OQ1 | Who marks an order as shipped, and from where? | Shop staff, Order | No caller of the ship action was found |
| OQ2 | Does cancelling refund the customer? | FR3 | The only test for it is skipped |
| OQ3 | What does the customer see when an order isn't found? | ERR4 | The message key has no wording in the catalog |

## Gaps & conflicts

| Kind | Detail | Search run |
|---|---|---|
| Gap | No caller of the ship action | `grep -rn "Ship()" src/` found only the definition |
| Gap | Refund on cancel is tested only by a skipped test | `src/shop-api/tests/OrdersControllerTests.cs:15` |
| Gap | Legacy order endpoint is marked obsolete and returns "gone" | `grep -rn "orders/legacy" src/shop-app` found no caller |
