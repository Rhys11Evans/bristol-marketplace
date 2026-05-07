from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Product
from .services import reduce_product_stock


class ProductOfficialTestCases(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = APIClient()

        self.producer = User.objects.create_user(
            username="producer",
            email="producer@test.com",
            password="testpass123",
            role="PRODUCER",
        )

        self.customer = User.objects.create_user(
            username="customer",
            email="customer@test.com",
            password="testpass123",
            role="CUSTOMER",
        )

        self.fruit = Category.objects.create(name="Fruit")
        self.dairy = Category.objects.create(name="Dairy")

        self.apple = Product.objects.create(
            name="Fresh Apples",
            category=self.fruit,
            producer=self.producer,
            description="Fresh organic apples",
            price=1.50,
            unit="item",
            stock_quantity=20,
            is_available=True,
            availability_status="available",
            allergen_info="No common allergens",
        )

        self.milk = Product.objects.create(
            name="Fresh Milk",
            category=self.dairy,
            producer=self.producer,
            description="Local dairy milk",
            price=1.20,
            unit="bottle",
            stock_quantity=10,
            is_available=True,
            availability_status="available",
            allergen_info="Contains milk",
        )

    # TC-003: Producer can list a new product
    def test_tc003_producer_can_create_product(self):
        self.client.force_authenticate(user=self.producer)

        data = {
            "name": "Organic Free Range Eggs",
            "category_id": self.dairy.id,
            "description": "Fresh organic eggs from free-range hens",
            "price": "3.50",
            "unit": "dozen",
            "stock_quantity": 50,
            "is_available": True,
            "availability_status": "available",
            "allergen_info": "Contains eggs",
        }

        response = self.client.post("/api/products/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(name="Organic Free Range Eggs").count(), 1)

    # TC-004: Browse products by category
    def test_tc004_filter_products_by_category(self):
        response = self.client.get("/api/products/?category=Fruit")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [item["name"] for item in response.data]

        self.assertIn("Fresh Apples", product_names)
        self.assertNotIn("Fresh Milk", product_names)

    # TC-005: Search products
    def test_tc005_search_products_by_name_description_or_producer(self):
        response = self.client.get("/api/products/?search=organic")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [item["name"] for item in response.data]

        self.assertIn("Fresh Apples", product_names)

    def test_tc005_search_no_results_returns_empty_list(self):
        response = self.client.get("/api/products/?search=nonexistentproduct")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # TC-011: Inventory updates and validation
    def test_tc011_negative_stock_is_rejected(self):
        self.client.force_authenticate(user=self.producer)

        data = {
            "name": "Invalid Stock Product",
            "category_id": self.fruit.id,
            "description": "Bad stock test",
            "price": "2.00",
            "unit": "item",
            "stock_quantity": -1,
            "is_available": True,
            "availability_status": "available",
            "allergen_info": "",
        }

        response = self.client.post("/api/products/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stock_quantity", response.data)

    def test_tc011_unavailable_product_not_returned_as_available_filter(self):
        self.apple.is_available = False
        self.apple.availability_status = "unavailable"
        self.apple.save()

        response = self.client.get("/api/products/?is_available=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [item["name"] for item in response.data]

        self.assertNotIn("Fresh Apples", product_names)

    # TC-015: Allergen information is stored and returned
    def test_tc015_allergen_information_displayed_in_api(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        milk_product = next(item for item in response.data if item["name"] == "Fresh Milk")
        self.assertEqual(milk_product["allergen_info"], "Contains milk")

    # TC-016: Seasonal availability values and months
    def test_tc016_seasonal_product_with_valid_months_is_created(self):
        self.client.force_authenticate(user=self.producer)

        data = {
            "name": "Seasonal Strawberries",
            "category_id": self.fruit.id,
            "description": "Local seasonal strawberries",
            "price": "4.00",
            "unit": "box",
            "stock_quantity": 15,
            "is_available": True,
            "availability_status": "in_season",
            "season_start_month": 6,
            "season_end_month": 8,
            "allergen_info": "No common allergens",
        }

        response = self.client.post("/api/products/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(name="Seasonal Strawberries")
        self.assertEqual(product.season_start_month, 6)
        self.assertEqual(product.season_end_month, 8)

    def test_tc016_invalid_season_month_is_rejected(self):
        self.client.force_authenticate(user=self.producer)

        data = {
            "name": "Invalid Season Product",
            "category_id": self.fruit.id,
            "description": "Invalid month test",
            "price": "4.00",
            "unit": "box",
            "stock_quantity": 15,
            "is_available": True,
            "availability_status": "in_season",
            "season_start_month": 13,
            "season_end_month": 8,
            "allergen_info": "",
        }

        response = self.client.post("/api/products/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("season_start_month", response.data)

    # TC-023: Stock reduction when orders are placed
    def test_tc023_reduce_product_stock_after_order(self):
        reduce_product_stock(self.apple, 5)

        self.apple.refresh_from_db()
        self.assertEqual(self.apple.stock_quantity, 15)

    def test_tc023_stock_reaches_zero_product_becomes_unavailable(self):
        reduce_product_stock(self.apple, 20)

        self.apple.refresh_from_db()
        self.assertEqual(self.apple.stock_quantity, 0)
        self.assertFalse(self.apple.is_available)
        self.assertEqual(self.apple.availability_status, "unavailable")

    def test_tc023_order_cannot_reduce_more_than_available_stock(self):
        with self.assertRaises(ValueError):
            reduce_product_stock(self.apple, 100)