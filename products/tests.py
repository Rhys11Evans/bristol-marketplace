from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product


class ProductAPITests(APITestCase):
    def setUp(self):
        self.category_fruit = Category.objects.create(name="Fruit")
        self.category_veg = Category.objects.create(name="Vegetables")

        self.owner = User.objects.create_user(
            username="producer1",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="producer2",
            password="testpass123"
        )

        self.apple = Product.objects.create(
            name="Apple",
            category=self.category_fruit,
            producer=self.owner,
            price=Decimal("1.50"),
            stock_quantity=10,
            is_available=True,
        )

        self.carrot = Product.objects.create(
            name="Carrot",
            category=self.category_veg,
            producer=self.other_user,
            price=Decimal("0.80"),
            stock_quantity=20,
            is_available=True,
        )

        self.unavailable_product = Product.objects.create(
            name="Old Potato",
            category=self.category_veg,
            producer=self.owner,
            price=Decimal("0.50"),
            stock_quantity=0,
            is_available=False,
        )

        self.category_url = reverse("category-list")
        self.product_list_url = reverse("product-list")
        self.product_detail_url = reverse("product-detail", args=[self.apple.id])

    def test_category_list_returns_success(self):
        response = self.client.get(self.category_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_product_list_returns_success(self):
        response = self.client.get(self.product_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_product_detail_returns_success(self):
        response = self.client.get(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Apple")

    def test_category_filtering_works(self):
        response = self.client.get(self.product_list_url, {"category": "Fruit"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Apple")

    def test_search_works_by_product_name(self):
        response = self.client.get(self.product_list_url, {"search": "app"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Apple")

    def test_search_works_by_category_name(self):
        response = self.client.get(self.product_list_url, {"search": "veget"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_works_by_producer_username(self):
        response = self.client.get(self.product_list_url, {"search": "producer1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_availability_filter_true_works(self):
        response = self.client.get(self.product_list_url, {"is_available": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_availability_filter_false_works(self):
        response = self.client.get(self.product_list_url, {"is_available": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Old Potato")

    def test_ordering_by_price_works(self):
        response = self.client.get(self.product_list_url, {"ordering": "price"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(item["price"]) for item in response.data]
        self.assertEqual(prices, sorted(prices))

    def test_logged_in_user_can_create_product(self):
        self.client.login(username="producer1", password="testpass123")

        payload = {
            "name": "Pear",
            "price": "2.10",
            "stock_quantity": 5,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.post(self.product_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(name="Pear").count(), 1)

        product = Product.objects.get(name="Pear")
        self.assertEqual(product.producer, self.owner)

    def test_anonymous_user_cannot_create_product(self):
        payload = {
            "name": "Pear",
            "price": "2.10",
            "stock_quantity": 5,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.post(self.product_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_product(self):
        self.client.login(username="producer1", password="testpass123")

        payload = {
            "name": "Green Apple",
            "price": "1.60",
            "stock_quantity": 12,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.put(self.product_detail_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.apple.refresh_from_db()
        self.assertEqual(self.apple.name, "Green Apple")

    def test_non_owner_cannot_update_product(self):
        self.client.login(username="producer2", password="testpass123")

        payload = {
            "name": "Bad Update",
            "price": "1.60",
            "stock_quantity": 12,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.put(self.product_detail_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_product(self):
        self.client.login(username="producer1", password="testpass123")

        response = self.client.delete(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.apple.id).exists())

    def test_non_owner_cannot_delete_product(self):
        self.client.login(username="producer2", password="testpass123")

        response = self.client.delete(self.product_detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_price_validation_rejects_zero_or_less(self):
        self.client.login(username="producer1", password="testpass123")

        payload = {
            "name": "Invalid Price Product",
            "price": "0.00",
            "stock_quantity": 5,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.post(self.product_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_stock_validation_rejects_negative_values(self):
        self.client.login(username="producer1", password="testpass123")

        payload = {
            "name": "Invalid Stock Product",
            "price": "1.00",
            "stock_quantity": -1,
            "is_available": True,
            "category_id": self.category_fruit.id,
        }

        response = self.client.post(self.product_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stock_quantity", response.data)
