from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    producer_username = serializers.ReadOnlyField(source='producer.username')

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'producer', 'producer_username', 'created_at']
        read_only_fields = ['producer', 'producer_username', 'created_at']
