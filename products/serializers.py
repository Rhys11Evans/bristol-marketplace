from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
    )
    producer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "unit",
            "stock_quantity",
            "is_available",
            "availability_status",
            "allergen_info",
            "harvest_date",
            "season_start_month",
            "season_end_month",
            "category",
            "category_id",
            "producer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Product name cannot be blank.")
        return value.strip()

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

    def validate_allergen_info(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()

    def validate_season_start_month(self, value):
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("Season start month must be between 1 and 12.")
        return value

    def validate_season_end_month(self, value):
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("Season end month must be between 1 and 12.")
        return value

    def validate(self, attrs):
        season_start_month = attrs.get("season_start_month")
        season_end_month = attrs.get("season_end_month")
        availability_status = attrs.get("availability_status")
        stock_quantity = attrs.get("stock_quantity")
        is_available = attrs.get("is_available")

        if (season_start_month is None) != (season_end_month is None):
            raise serializers.ValidationError(
                "Both season start month and season end month must be provided together."
            )

        if availability_status == "unavailable":
            if is_available is True:
                raise serializers.ValidationError(
                    {"is_available": "Unavailable products cannot be marked as available."}
                )

        if stock_quantity == 0 and availability_status == "available" and is_available is True:
            raise serializers.ValidationError(
                {
                    "stock_quantity": "Available products should have stock greater than 0."
                }
            )

        return attrs