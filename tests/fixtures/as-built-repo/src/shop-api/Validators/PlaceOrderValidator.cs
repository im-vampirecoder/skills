using FluentValidation;

namespace ShopApi.Validators;

public class PlaceOrderValidator : AbstractValidator<PlaceOrderRequest>
{
    public PlaceOrderValidator()
    {
        RuleFor(x => x.Items).NotEmpty().WithMessage("orders.empty_cart");
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.Quantity).InclusiveBetween(1, 99);
        });
        RuleFor(x => x.DeliveryPostcode).NotEmpty().Length(4, 10);
    }
}
