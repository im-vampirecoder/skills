namespace ShopApi.Domain;

public enum OrderStatus
{
    Placed,
    Shipped,
    Cancelled
}

public class Order
{
    public Guid Id { get; private set; } = Guid.NewGuid();
    public string CustomerId { get; private set; } = "";
    public List<OrderItem> Items { get; private set; } = new();
    public OrderStatus Status { get; private set; } = OrderStatus.Placed;

    public static Order Create(string customerId, List<OrderItem> items) =>
        new() { CustomerId = customerId, Items = items };

    public void Ship() => Status = OrderStatus.Shipped;

    public void Cancel() => Status = OrderStatus.Cancelled;
}

public record OrderItem(string ProductId, int Quantity);
