from django.db import transaction


def reduce_product_stock(product, quantity):
    """
    Reduces stock for a product.

    This is kept inside the products app so cart/order code can call it
    without needing to duplicate product stock logic.
    """

    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    with transaction.atomic():
        product = product.__class__.objects.select_for_update().get(pk=product.pk)

        if product.stock_quantity < quantity:
            raise ValueError(
                f"Not enough stock available for {product.name}. "
                f"Only {product.stock_quantity} left."
            )

        product.stock_quantity -= quantity

        if product.stock_quantity == 0:
            product.is_available = False
            product.availability_status = "unavailable"

        product.save(
            update_fields=[
                "stock_quantity",
                "is_available",
                "availability_status",
                "updated_at",
            ]
        )

    return product