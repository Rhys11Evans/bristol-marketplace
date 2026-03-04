from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsProducer

from .models import Product
from .serializers import ProductSerializer


class ProductCreateView(APIView):
    """
    POST /api/products/create/
    S1-T3: Only PRODUCER can create products.
    Customer gets 403 Forbidden.
    """
    permission_classes = [IsAuthenticated, IsProducer]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(producer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductListView(APIView):
    """
    GET /api/products/
    Anyone authenticated can view products.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.select_related('producer').all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
