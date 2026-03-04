from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer


class ProductListAPIView(generics.ListAPIView):
    """
    READ ONLY endpoint for Sprint 1:
    - GET /api/products/ returns all products as JSON
    """

    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer