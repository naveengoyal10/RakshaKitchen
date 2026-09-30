import json
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, CustomerInquiry, FoodItem, FoodVariant, Order, OrderItem


class OrderingFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.food_item = FoodItem.objects.create(
            category=self.category,
            name="Test Samosa",
            slug="test-samosa",
            description="Test food",
            price=Decimal("50.00"),
            available=True,
        )
        self.second_item = FoodItem.objects.create(
            category=self.category,
            name="Test Kebab",
            slug="test-kebab",
            description="Test food",
            price=Decimal("80.00"),
            available=True,
        )
        self.variant = FoodVariant.objects.create(food_item=self.second_item, name="Large", price=Decimal("120.00"), active=True)

    def test_order_calculates_multiple_items_from_database_prices(self):
        response = self.client.post(reverse("kitchen:order"), {
            "customer_name": "Asha",
            "mobile": "9876543210",
            "address": "Test address",
            "preferred_date": (date.today() + timedelta(days=2)).isoformat(),
            "order_type": "delivery",
            "notes": "Pack carefully",
            "cart_data": json.dumps([
                {"food_item_id": self.food_item.pk, "variant_id": None, "quantity": 2, "price": 0},
                {"food_item_id": self.second_item.pk, "variant_id": self.variant.pk, "quantity": 3, "price": 1},
            ]),
        })
        order = Order.objects.get()
        self.assertRedirects(response, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertEqual(order.total_amount, Decimal("460.00"))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.items.get(food_item=self.second_item).price, Decimal("120.00"))

    def test_mismatched_variant_is_rejected(self):
        response = self.client.post(reverse("kitchen:order"), {
            "customer_name": "Asha",
            "mobile": "9876543210",
            "address": "Test address",
            "order_type": "delivery",
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "variant_id": self.variant.pk, "quantity": 1}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "selected sizes is no longer available")

    def test_product_pages_show_cart_and_buy_now_controls(self):
        self.food_item.featured = True
        self.food_item.save(update_fields=["featured"])
        product_pages = [
            reverse("kitchen:home"),
            reverse("kitchen:menu"),
            reverse("kitchen:menu_detail", args=[self.food_item.slug]),
            reverse("kitchen:bulk_orders"),
        ]
        for url in product_pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "Add to Cart")
                self.assertContains(response, "Buy Now")

    def test_detail_page_only_offers_active_variants(self):
        active_variant = FoodVariant.objects.create(food_item=self.food_item, name="Active size", price=Decimal("75.00"), active=True)
        FoodVariant.objects.create(food_item=self.food_item, name="Retired size", price=Decimal("90.00"), active=False)

        response = self.client.get(reverse("kitchen:menu_detail", args=[self.food_item.slug]))

        self.assertContains(response, active_variant.name)
        self.assertNotContains(response, "Retired size")

    def test_order_item_rejects_variant_from_another_food(self):
        item = OrderItem(order=Order(customer_name="A", mobile="9876543210", address="A"), food_item=self.food_item, variant=self.variant, quantity=1, price=Decimal("50"), subtotal=Decimal("50"))
        with self.assertRaises(ValidationError):
            item.full_clean()


class BulkInquiryTests(TestCase):
    def test_bulk_form_saves_customer_inquiry(self):
        response = self.client.post(reverse("kitchen:bulk_orders"), {
            "name": "Priya",
            "mobile": "9876543210",
            "email": "priya@example.com",
            "event_type": "office",
            "event_date": (date.today() + timedelta(days=5)).isoformat(),
            "number_of_people": 30,
            "food_requirements": "Snacks and sweets",
            "budget": "15000",
            "address": "Office venue",
            "additional_notes": "Vegetarian options",
        })
        self.assertRedirects(response, reverse("kitchen:bulk_orders"), fetch_redirect_response=False)
        self.assertEqual(CustomerInquiry.objects.get().status, "new")
