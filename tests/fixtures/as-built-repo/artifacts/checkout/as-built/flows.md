# Checkout - flows

## Flow: place-order

A customer reviews the cart and places an order.

### Sequence

```mermaid
sequenceDiagram
    actor Customer
    participant App as Mobile app
    participant Shop as Shop service
    Customer->>App: Taps Place order
    App->>Shop: Sends the cart
    alt Cart empty or over 20 items
        Shop-->>App: Rejects with a reason
        App-->>Customer: Shows the error message
    else Cart valid
        Shop-->>App: Order placed
        App-->>Customer: Shows the order confirmation
    end
```

### Activity

```mermaid
flowchart TD
    A(["Customer taps Place order"]) --> B{"Cart empty?"}
    B -->|"Yes"| E1["Show: Your cart is empty"]
    B -->|"No"| C{"More than 20 items?"}
    C -->|"Yes"| E2["Show: at most 20 items"]
    C -->|"No"| D["Save order as Placed"]
    D --> F(["Show order confirmation"])
```

## Flow: cancel-order

A customer cancels an order that is still placed.

### Sequence

```mermaid
sequenceDiagram
    actor Customer
    participant Shop as Shop service
    Customer->>Shop: Asks to cancel the order
    alt Order still placed
        Shop-->>Customer: Order cancelled
    else Shipped, cancelled or missing
        Shop-->>Customer: This order can no longer be cancelled
    end
```

### Activity

```mermaid
flowchart TD
    A(["Customer cancels"]) --> B{"Order still placed?"}
    B -->|"Yes"| C["Mark order Cancelled"]
    B -->|"No"| E["Show: can no longer be cancelled"]
    C --> D(["Done"])
```
