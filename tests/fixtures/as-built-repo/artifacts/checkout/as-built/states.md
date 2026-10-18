# Checkout - states

## State: Order

```mermaid
stateDiagram-v2
    [*] --> Placed : Order placed
    Placed --> Cancelled : Customer cancels
    Placed --> Shipped : Dispatched
    Cancelled --> [*]
    Shipped --> [*]
```

| From | To | Label | Source |
|---|---|---|---|
| (new) | Placed | ✅ | `src/shop-api/Domain/Order.cs:15` |
| Placed | Cancelled | ✅ | `src/shop-api/Domain/Order.cs:22` |
| Placed | Shipped | 🔵 | `src/shop-api/Domain/Order.cs:20`, `src/shop-api/Domain/Order.cs:6` |
