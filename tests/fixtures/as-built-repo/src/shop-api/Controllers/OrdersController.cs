using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using ShopApi.Domain;
using ShopApi.Validators;

namespace ShopApi.Controllers;

[ApiController]
[Route("api/orders")]
[Authorize]
public class OrdersController : ControllerBase
{
    private const int MaxItemsPerOrder = 20;
    private readonly IOrderStore _orders;

    public OrdersController(IOrderStore orders) => _orders = orders;

    [HttpPost]
    public async Task<IActionResult> PlaceOrder(PlaceOrderRequest request)
    {
        if (request.Items.Count > MaxItemsPerOrder)
        {
            return BadRequest(new { code = "orders.too_many_items" });
        }

        var order = Order.Create(User.Identity!.Name!, request.Items);
        await _orders.SaveAsync(order);
        return CreatedAtAction(nameof(GetOrder), new { id = order.Id }, order);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetOrder(Guid id)
    {
        var order = await _orders.FindAsync(id);
        return order is null ? NotFound(new { code = "orders.not_found" }) : Ok(order);
    }

    [HttpPost("{id}/cancel")]
    public async Task<IActionResult> CancelOrder(Guid id)
    {
        var order = await _orders.FindAsync(id);
        if (order is null || order.Status != OrderStatus.Placed)
        {
            return Conflict(new { code = "orders.cannot_cancel" });
        }

        order.Cancel();
        await _orders.SaveAsync(order);
        return NoContent();
    }

    [Obsolete("Use PlaceOrder")]
    [HttpPost("legacy")]
    public IActionResult PlaceOrderLegacy() => StatusCode(410);
}
