from django.conf import settings
from django.db import models


class Product(models.Model):
    """
    Minimal product model for S1-T3 demo.
    producer FK -> AUTH_USER_MODEL (only users with role=PRODUCER)
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name
