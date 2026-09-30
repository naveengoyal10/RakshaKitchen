import json
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, CustomerInquiry, FoodItem, FoodVariant, Order, OrderItem


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="orders@example.com", ADMIN_ORDER_EMAIL="admin@example.com", RESEND_API_KEY="", RESEND_FROM_EMAIL="")
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

    def post_order(self, data):
        self.client.get(reverse("kitchen:order"))
        payload = {
            "customer_name": "Asha",
            "mobile": "9876543210",
            "email": "asha@example.com",
            "address": "Test address",
            "building_society": "Life Republic",
            "flat_number": "A-101",
            "preferred_date": (date.today() + timedelta(days=1)).isoformat(),
            "preferred_time": "18:00",
            "order_type": "delivery",
            "cart_data": "[]",
            **data,
            "submission_token": self.client.session["checkout_token"],
        }
        return self.client.post(reverse("kitchen:order"), payload)

    def test_order_calculates_multiple_items_from_database_prices(self):
        response = self.post_order({
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
        self.assertEqual(order.status, "pending")
        self.assertTrue(order.order_number.startswith(f"RK-{date.today():%Y%m%d}-"))
        self.assertEqual(order.items.get(food_item=self.second_item).product_name, self.second_item.name)

    def test_mismatched_variant_is_rejected(self):
        response = self.post_order({
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

    def test_shared_mobile_cart_access_and_checkout_action_are_present(self):
        home_response = self.client.get(reverse("kitchen:home"))
        self.assertContains(home_response, 'class="mobile-cart-link" href="/cart"')
        self.assertContains(home_response, "data-sticky-cart")

        checkout_response = self.client.get(reverse("kitchen:order"))
        self.assertContains(checkout_response, "PLACE ORDER")
        self.assertContains(checkout_response, "data-mobile-place-order")

    def test_detail_page_only_offers_active_variants(self):
        active_variant = FoodVariant.objects.create(food_item=self.food_item, name="Active size", price=Decimal("75.00"), active=True)
        FoodVariant.objects.create(food_item=self.food_item, name="Retired size", price=Decimal("90.00"), active=False)

        response = self.client.get(reverse("kitchen:menu_detail", args=[self.food_item.slug]))

        self.assertContains(response, active_variant.name)
        self.assertNotContains(response, "Retired size")

    def test_cart_page_has_empty_state_and_continue_shopping(self):
        response = self.client.get(reverse("kitchen:cart"))

        self.assertContains(response, "Your cart is empty.")
        self.assertContains(response, "Continue Shopping")
        self.assertEqual(reverse("kitchen:cart"), "/cart")

    def test_cart_api_uses_database_prices_and_merges_duplicate_items(self):
        response = self.client.post(reverse("kitchen:cart"), json.dumps({
            "cart": [
                {"food_item_id": self.food_item.pk, "variant_id": None, "quantity": 2, "price": "0.01"},
                {"food_item_id": self.food_item.pk, "variant_id": None, "quantity": 2, "price": "9999.00"},
                {"food_item_id": self.second_item.pk, "variant_id": self.variant.pk, "quantity": 1, "price": "0"},
            ],
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        snapshot = response.json()
        self.assertEqual(snapshot["total"], "320.00")
        self.assertEqual(len(snapshot["items"]), 2)
        self.assertEqual(snapshot["items"][0]["quantity"], 4)
        self.assertEqual(snapshot["items"][0]["price"], "50.00")

        cart_page = self.client.get(reverse("kitchen:cart"))
        self.assertContains(cart_page, "Test Samosa")
        self.assertContains(cart_page, "200.00")

    def test_minimum_quantity_is_enforced_by_cart_and_checkout(self):
        self.food_item.minimum_quantity = 4
        self.food_item.save(update_fields=["minimum_quantity"])
        cart_response = self.client.post(reverse("kitchen:cart"), json.dumps({
            "cart": [{"food_item_id": self.food_item.pk, "quantity": 1}],
        }), content_type="application/json")
        self.assertEqual(cart_response.status_code, 200)
        self.assertEqual(cart_response.json()["items"][0]["quantity"], 4)
        self.assertTrue(cart_response.json()["warnings"])

        response = self.post_order({
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 3}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "minimum order quantity of 4")

    def test_checkout_reloads_price_after_cart_add_and_rejects_unavailable_products(self):
        cart_response = self.client.post(reverse("kitchen:cart"), json.dumps({
            "cart": [{"food_item_id": self.food_item.pk, "quantity": 2, "price": "1.00"}],
        }), content_type="application/json")
        self.assertEqual(cart_response.status_code, 200)
        self.food_item.price = Decimal("75.00")
        self.food_item.save(update_fields=["price"])

        response = self.post_order({
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 2, "price": "1.00"}]),
        })
        order = Order.objects.get()
        self.assertEqual(order.total_amount, Decimal("150.00"))
        self.assertEqual(order.items.get().price, Decimal("75.00"))

        self.food_item.available = False
        self.food_item.save(update_fields=["available"])
        self.client.get(reverse("kitchen:order"))
        unavailable = self.client.post(reverse("kitchen:order"), {
            "customer_name": "Asha", "mobile": "9876543210", "email": "asha@example.com",
            "address": "Test address", "building_society": "Life Republic", "flat_number": "A-101",
            "preferred_date": (date.today() + timedelta(days=1)).isoformat(), "preferred_time": "18:00",
            "order_type": "delivery", "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 1}]),
            "submission_token": self.client.session["checkout_token"],
        })
        self.assertEqual(unavailable.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        self.assertContains(unavailable, "no longer available")

    def test_invalid_customer_email_prevents_order_creation(self):
        response = self.post_order({
            "email": "not-an-email",
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 1}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address")

    def test_checkout_without_cart_items_does_not_create_order(self):
        response = self.post_order({"cart_data": "[]"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "Add at least one food item before submitting")
        self.assertContains(response, "We couldn't place your order yet")

    def test_duplicate_checkout_submission_creates_only_one_order(self):
        self.client.get(reverse("kitchen:order"))
        data = {
            "customer_name": "Asha",
            "mobile": "9876543210",
            "email": "asha@example.com",
            "address": "Test address",
            "building_society": "Life Republic",
            "flat_number": "A-101",
            "preferred_date": (date.today() + timedelta(days=1)).isoformat(),
            "preferred_time": "18:00",
            "order_type": "delivery",
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 1}]),
            "submission_token": self.client.session["checkout_token"],
        }
        first = self.client.post(reverse("kitchen:order"), data)
        second = self.client.post(reverse("kitchen:order"), data)
        self.assertRedirects(first, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertRedirects(second, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="orders@example.com", ADMIN_ORDER_EMAIL="admin@example.com", RAKSHA_PHONE="+91 93051 26262")
    def test_customer_and_admin_email_sent_after_order_is_saved(self):
        response = self.post_order({
            "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 2}]),
        })
        order = Order.objects.get()
        self.assertRedirects(response, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertTrue(order.customer_email_sent)
        self.assertTrue(order.admin_email_sent)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(order.order_number, mail.outbox[0].subject)
        self.assertIn("₹100.00", mail.outbox[0].body)
        self.assertIn("A-101", mail.outbox[1].body)
        self.assertNotIn("cart", self.client.session)
        confirmation = self.client.get(reverse("kitchen:order_success"))
        self.assertContains(confirmation, "Order successfully")
        self.assertContains(confirmation, order.order_number)
        self.assertContains(confirmation, "Test Samosa")
        self.assertContains(confirmation, "Pending")
        self.assertContains(confirmation, "Life Republic")

    @override_settings(RESEND_API_KEY="re_test_key", RESEND_FROM_EMAIL="Raksha Kitchen <orders@example.com>")
    def test_customer_and_admin_emails_use_resend_https_api_when_configured(self):
        from unittest.mock import patch

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"id":"test-email-id"}'

        with patch("kitchen.order_emails.urlopen", return_value=FakeResponse()) as urlopen:
            response = self.post_order({
                "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 2}]),
            })

        order = Order.objects.get()
        self.assertRedirects(response, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertTrue(order.customer_email_sent)
        self.assertTrue(order.admin_email_sent)
        self.assertEqual(urlopen.call_count, 2)
        self.assertTrue(all(call.args[0].full_url == "https://api.resend.com/emails" for call in urlopen.call_args_list))
        self.assertTrue(all(call.args[0].get_header("Authorization") == "Bearer re_test_key" for call in urlopen.call_args_list))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="orders@example.com", ADMIN_ORDER_EMAIL="admin@example.com")
    def test_email_failure_does_not_lose_order_or_retain_cart(self):
        from unittest.mock import patch

        with self.assertLogs("kitchen.order_emails", level="ERROR"):
            with patch("kitchen.order_emails.send_mail", side_effect=OSError("mail service unavailable")):
                response = self.post_order({
                    "cart_data": json.dumps([{"food_item_id": self.food_item.pk, "quantity": 1}]),
                })
        order = Order.objects.get()
        self.assertRedirects(response, reverse("kitchen:order_success"), fetch_redirect_response=False)
        self.assertEqual(order.items.count(), 1)
        self.assertFalse(order.customer_email_sent)
        self.assertFalse(order.admin_email_sent)
        self.assertTrue(order.email_error)
        self.assertNotIn("cart", self.client.session)

        with patch("kitchen.order_emails.send_mail", return_value=1) as send_mail_mock:
            from .order_emails import send_order_notifications
            self.assertTrue(send_order_notifications(order))
        self.assertEqual(send_mail_mock.call_count, 2)
        order.refresh_from_db()
        self.assertTrue(order.customer_email_sent)
        self.assertTrue(order.admin_email_sent)

    def test_unavailable_items_are_removed_from_cart_sync(self):
        self.client.post(reverse("kitchen:cart"), json.dumps({
            "cart": [{"food_item_id": self.food_item.pk, "quantity": 1}],
        }), content_type="application/json")
        self.food_item.available = False
        self.food_item.save(update_fields=["available"])

        response = self.client.post(reverse("kitchen:cart"), json.dumps({
            "cart": [{"food_item_id": self.food_item.pk, "quantity": 1}],
        }), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        self.assertTrue(response.json()["warnings"])

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
