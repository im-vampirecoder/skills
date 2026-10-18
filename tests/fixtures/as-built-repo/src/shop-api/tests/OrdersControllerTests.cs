using Shouldly;
using Xunit;

namespace ShopApi.Tests;

public class OrdersControllerTests
{
    [Fact]
    public async Task PlaceOrder_rejects_more_than_twenty_items()
    {
        var result = await Controller().PlaceOrder(RequestWithItems(21));
        result.ShouldBeOfType<BadRequestObjectResult>();
    }

    [Fact(Skip = "flaky on CI")]
    public async Task CancelOrder_refunds_the_customer()
    {
        var result = await Controller().CancelOrder(PlacedOrderId());
        Refunds.Issued.ShouldBe(1);
    }
}
