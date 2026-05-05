from django.db.models import Q
from django.utils import timezone

from rest_framework import filters, generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsProducer

from .models import Category, Product
from .permissions import IsProducerForWriteOrReadOnly
from .serializers import CategorySerializer, ProductSerializer


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsProducerForWriteOrReadOnly]
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
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
                | Q(producer__username__icontains=search)
            )

        if is_available is not None:
            value = is_available.lower()

            if value == "true":
                queryset = queryset.filter(is_available=True)
            elif value == "false":
                queryset = queryset.filter(is_available=False)
            else:
                raise ValidationError(
                    {
                        "is_available": "Use true or false for this filter."
                    }
                )

        if availability_status:
            valid_statuses = [choice[0] for choice in Product.AVAILABILITY_CHOICES]

            if availability_status not in valid_statuses:
                raise ValidationError(
                    {
                        "availability_status": f"Invalid value. Use one of: {', '.join(valid_statuses)}."
                    }
                )

            queryset = queryset.filter(availability_status=availability_status)

        current_month = timezone.now().month

        queryset = queryset.filter(
            Q(availability_status="available")
            | Q(availability_status="unavailable")
            | Q(
                availability_status="in_season",
                season_start_month__isnull=True,
                season_end_month__isnull=True,
            )
            | Q(
                availability_status="in_season",
                season_start_month__lte=current_month,
                season_end_month__gte=current_month,
            )
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(producer=self.request.user)


class ProductCreateView(APIView):
    permission_classes = [IsProducer]

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(producer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category", "producer").all()
    serializer_class = ProductSerializer
    permission_classes = [IsProducerForWriteOrReadOnly]