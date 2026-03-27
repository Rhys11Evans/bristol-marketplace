from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    # Shop
    path("shop/", views.product_list, name="product_list"),
    path("shop/add/", views.add_to_cart, name="add_to_cart"),

    # Carts
    path("carts/", views.cart_list, name="cart_list"),
    path("carts/create/", views.create_cart, name="create_cart"),
    path("carts/<int:cart_id>/", views.cart_detail, name="cart_detail"),
    path("carts/<int:cart_id>/delete/", views.delete_cart, name="delete_cart"),
    path("carts/<int:cart_id>/checkout/", views.checkout, name="checkout"),

    # Cart items
    path("cart-item/<int:item_id>/update/", views.update_cart_item, name="update_cart_item"),
    path("cart-item/<int:item_id>/remove/", views.remove_cart_item, name="remove_cart_item"),

    # Orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
]
