from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("api/cart/", include("cart.urls")),
]