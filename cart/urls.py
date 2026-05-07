from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    # Home redirect (sends to shop or producer orders based on role)
    path("", views.home, name="home"),

    # Logout
    path("logout/", views.logout_view, name="logout"),

    # Shop (customers)
    path("shop/", views.product_list, name="product_list"),
    path("shop/add/", views.add_to_cart, name="add_to_cart"),

    # Carts (customers)
    path("carts/", views.cart_list, name="cart_list"),
    path("carts/create/", views.create_cart, name="create_cart"),
    path("carts/<int:cart_id>/", views.cart_detail, name="cart_detail"),
    path("carts/<int:cart_id>/delete/", views.delete_cart, name="delete_cart"),
    path("carts/<int:cart_id>/checkout/", views.checkout, name="checkout"),

    # Cart items (customers)
    path("cart-item/<int:item_id>/update/", views.update_cart_item, name="update_cart_item"),
    path("cart-item/<int:item_id>/remove/", views.remove_cart_item, name="remove_cart_item"),

    # Orders (customers)
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_confirmation, name="order_confirmation"),

    # Producer order management
    path("producer/orders/", views.producer_order_list, name="producer_order_list"),
    path("producer/orders/<int:order_id>/", views.producer_order_detail, name="producer_order_detail"),
    path("producer/item/<int:item_id>/update-status/", views.update_item_status, name="update_item_status"),
]