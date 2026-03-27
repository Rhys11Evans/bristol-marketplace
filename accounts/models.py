from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role field.
    S1-T2: Add role field (customer/producer)
    """

    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        PRODUCER = 'PRODUCER', 'Producer'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.username} ({self.role})'

    @property
    def is_producer(self):
        return self.role == self.Role.PRODUCER

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER
