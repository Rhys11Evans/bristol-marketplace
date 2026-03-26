from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsOwnerOrReadOnly


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer


class ProductListAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["name", "price", "stock_quantity", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = Product.objects.select_related("category", "producer").all()

        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")
        is_available = self.request.query_params.get("is_available")
        availability_status = self.request.query_params.get("availability_status")

        if category:
            queryset = queryset.filter(category__name__iexact=category)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search) |
                Q(producer__username__icontains=search)
            )

        if is_available is not None:
            if is_available.lower() == "true":
                queryset = queryset.filter(is_available=True)
            elif is_available.lower() == "false":
                queryset = queryset.filter(is_available=False)

        if availability_status:
            queryset = queryset.filter(availability_status=availability_status)

        current_month = timezone.now().month

        queryset = queryset.filter(
            Q(availability_status="available") |
            Q(availability_status="unavailable") |
            Q(
                availability_status="in_season",
                season_start_month__isnull=True,
                season_end_month__isnull=True,
            ) |
            Q(
                availability_status="in_season",
                season_start_month__lte=current_month,
                season_end_month__gte=current_month,
            )
        )

        return queryset


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category", "producer").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]