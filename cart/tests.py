from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from products.models import Category, Product
from .models import Cart, CartItem, Order, OrderItem

User = get_user_model()


class CartTests(TestCase):

    def setUp(self):
        # create a customer and a producer
        self.user = User.objects.create_user(username="testuser", password="pass1234", role="CUSTOMER")
        self.producer = User.objects.create_user(username="testproducer", password="pass1234", role="PRODUCER")
        self.cat = Category.objects.create(name="Veg")
        self.product = Product.objects.create(
            name="Carrots", category=self.cat, price=2.50,
            stock_quantity=10, is_available=True, producer=self.producer,
        )
        self.client = Client()
        self.client.login(username="testuser", password="pass1234")

    #---------------------- adding to cart --------------------------
    def test_add_to_cart(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        resp = self.client.post("/shop/add/", {
            "product_id": self.product.pk,
            "cart_id": cart.pk,
            "quantity": 3,
        })
        self.assertEqual(resp.status_code, 302)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 3)

    #----------------- cant add more than stock --------------------
    def test_add_over_stock(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        resp = self.client.post("/shop/add/", {
            "product_id": self.product.pk,
            "cart_id": cart.pk,
            "quantity": 999,
        })
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())

    #-------------- cant checkout with empty cart -------------------
    def test_checkout_empty_cart(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        resp = self.client.post(f"/carts/{cart.pk}/checkout/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    #---------- checkout creates order and clears cart --------------
    def test_checkout_creates_order(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        resp = self.client.post(f"/carts/{cart.pk}/checkout/")
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_items.count(), 1)
        self.assertEqual(cart.items.count(), 0)

    #-------------- totals calculated correctly --------------------
    def test_order_totals(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        CartItem.objects.create(cart=cart, product=self.product, quantity=4)
        self.client.post(f"/carts/{cart.pk}/checkout/")
        order = Order.objects.first()
        # 4 x 2.50 = 10.00
        self.assertEqual(order.total_price, 10.00)
        # 5% of 10.00 = 0.50
        self.assertEqual(order.commission, 0.50)

    #-------------- per-item status progression --------------------
    def test_item_status_progression(self):
        # place an order as customer
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(f"/carts/{cart.pk}/checkout/")
        item = OrderItem.objects.first()
        self.assertEqual(item.status, "pending")

        # switch to producer to update status
        self.client.login(username="testproducer", password="pass1234")

        # pending -> confirmed
        self.client.post(f"/producer/item/{item.pk}/update-status/")
        item.refresh_from_db()
        self.assertEqual(item.status, "confirmed")

        # confirmed -> ready
        self.client.post(f"/producer/item/{item.pk}/update-status/")
        item.refresh_from_db()
        self.assertEqual(item.status, "ready")

        # ready -> delivered
        self.client.post(f"/producer/item/{item.pk}/update-status/")
        item.refresh_from_db()
        self.assertEqual(item.status, "delivered")

    #-------------- cant go past delivered -------------------------
    def test_cant_update_past_delivered(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(f"/carts/{cart.pk}/checkout/")
        item = OrderItem.objects.first()
        item.status = "delivered"
        item.save()

        # switch to producer
        self.client.login(username="testproducer", password="pass1234")
        self.client.post(f"/producer/item/{item.pk}/update-status/")
        item.refresh_from_db()
        self.assertEqual(item.status, "delivered")

    #---------------- update quantity in cart -----------------------
    def test_update_cart_quantity(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(f"/cart-item/{item.pk}/update/", {"quantity": 5})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    #-------------- cant set quantity over stock --------------------
    def test_update_over_stock(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(f"/cart-item/{item.pk}/update/", {"quantity": 999})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    #-------------- remove item from cart ---------------------------
    def test_remove_cart_item(self):
        cart = Cart.objects.create(user=self.user, name="Test Cart")
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.post(f"/cart-item/{item.pk}/remove/")
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())