from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("accounts/login/", LoginView.as_view(template_name="login/login.html"), name="login"),
    path("", include("cart.urls")),
]