from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("in_season", "In Season"),
        ("unavailable", "Unavailable"),
    ]

    UNIT_CHOICES = [
        ("kg", "Kilogram"),
        ("g", "Gram"),
        ("item", "Item"),
        ("box", "Box"),
        ("pack", "Pack"),
        ("bottle", "Bottle"),
        ("dozen", "Dozen"),
    ]

    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )

    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="item",
    )

    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default="available",
    )

    allergen_info = models.CharField(max_length=255, blank=True)
    harvest_date = models.DateField(null=True, blank=True)

    season_start_month = models.PositiveSmallIntegerField(null=True, blank=True)
    season_end_month = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name