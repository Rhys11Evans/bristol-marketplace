from django.db import models
from django.conf import settings
from decimal import Decimal

COMMISSION_RATE = Decimal("0.05")

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("ready", "Ready for Collection/Delivery"),
    ("delivered", "Delivered"),
]


#-------------------------- Cart --------------------------
class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    name = models.CharField(max_length=100, default="My Cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} – {self.user}"

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def is_empty(self):
        return not self.items.exists()


#----------------------- CartItem -------------------------
class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity


#-------------------------- Order --------------------------
class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} – {self.status}"

    def calculate_totals(self):
        self.total_price = sum(
            item.item_price * item.quantity
            for item in self.order_items.all()
        )
        self.commission = (self.total_price * COMMISSION_RATE).quantize(
            Decimal("0.01")
        )
        self.save(update_fields=["total_price", "commission"])

    @property
    def producer_payment(self):
        return self.total_price - self.commission


#----------------------- OrderItem -------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    item_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ £{self.item_price}"

    @property
    def line_total(self):
        return self.item_price * self.quantity
