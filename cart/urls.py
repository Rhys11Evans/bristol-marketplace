from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='view'),
    path('add/', views.AddToCartView.as_view(), name='add'),
    path('remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove'),
]
