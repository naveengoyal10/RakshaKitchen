import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.contrib import messages

from .forms import CustomerInquiryForm, OrderForm
from .models import Category, CustomerInquiry, FoodItem, FoodVariant, Order, OrderItem
from .order_emails import send_order_notifications
from .utils import build_order_whatsapp_url

logger = logging.getLogger(__name__)


def home(request):
    featured_items = FoodItem.objects.filter(available=True, featured=True).select_related("category").prefetch_related(Prefetch("variants", queryset=FoodVariant.objects.filter(active=True)))[:3]
    categories = Category.objects.filter(active=True)
    return render(request, "home.html", {"featured_items": featured_items, "categories": categories})


def about(request):
    return render(request, "about.html")


def menu(request):
    items = FoodItem.objects.filter(available=True).select_related("category").prefetch_related(Prefetch("variants", queryset=FoodVariant.objects.filter(active=True)))
    category = request.GET.get("category")
    categories = Category.objects.filter(active=True)
    if category:
        items = items.filter(category__slug=category)
    return render(request, "menu.html", {
        "items": items,
        "categories": categories,
        "active_category": category or "all",
    })


def menu_detail(request, slug):
    item = get_object_or_404(
        FoodItem.objects.prefetch_related(Prefetch("variants", queryset=FoodVariant.objects.filter(active=True))),
        slug=slug,
        available=True,
    )
    return render(request, "menu_detail.html", {"item": item})


def menu_pricing(request):
    items = FoodItem.objects.filter(available=True).values("id", "price", "unit_quantity", "unit", "base_option_name", "minimum_quantity")
    variants = FoodVariant.objects.filter(active=True, food_item__available=True).values("id", "price", "unit_quantity", "unit", "minimum_quantity")
    return JsonResponse({
        "items": {
            str(item["id"]): {
                "price": str(item["price"]),
                "unit_quantity": item["unit_quantity"],
                "unit": item["unit"],
                "base_option_name": item["base_option_name"],
                "minimum_quantity": item["minimum_quantity"],
            }
            for item in items
        },
        "variants": {
            str(variant["id"]): {
                "price": str(variant["price"]),
                "unit_quantity": variant["unit_quantity"],
                "unit": variant["unit"],
                "minimum_quantity": variant["minimum_quantity"],
            }
            for variant in variants
        },
    })


def bulk_orders(request):
    if request.method == "POST":
        form = CustomerInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your bulk enquiry has been received. We will be in touch shortly.")
            return redirect("kitchen:bulk_orders")
    else:
        form = CustomerInquiryForm()
    popular_items = FoodItem.objects.filter(available=True).prefetch_related(
        Prefetch("variants", queryset=FoodVariant.objects.filter(active=True))
    ).order_by("-featured", "display_order", "name")[:6]
    return render(request, "bulk_orders.html", {"form": form, "popular_items": popular_items})


def contact(request):
    return render(request, "contact.html")


def robots(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n",
        content_type="text/plain",
    )


def _resolve_cart_items(raw_cart, *, adjust_minimum=False, skip_unavailable=False, lock_rows=False):
    if not isinstance(raw_cart, list):
        raise ValueError("The cart data is invalid.")

    requested_items = {}
    for cart_item in raw_cart:
        if not isinstance(cart_item, dict):
            raise ValueError("The cart data is invalid.")
        try:
            food_item_id = int(cart_item.get("food_item_id"))
            variant_id = int(cart_item["variant_id"]) if cart_item.get("variant_id") else None
            quantity = int(cart_item.get("quantity"))
        except (KeyError, TypeError, ValueError):
            raise ValueError("The cart data is invalid.") from None
        if not 1 <= quantity <= 999:
            raise ValueError("Each quantity must be between 1 and 999.")

        key = (food_item_id, variant_id)
        requested_items[key] = requested_items.get(key, 0) + quantity
        if requested_items[key] > 999:
            raise ValueError("Each quantity must be between 1 and 999.")

    items = []
    warnings = []
    total = Decimal("0")
    for (food_item_id, variant_id), quantity in requested_items.items():
        food_item_query = FoodItem.objects.filter(pk=food_item_id, available=True).select_related("category")
        if lock_rows:
            food_item_query = food_item_query.select_for_update()
        food_item = food_item_query.first()
        if not food_item:
            if skip_unavailable:
                warnings.append("Unavailable products were removed from your cart.")
                continue
            raise ValueError("One of the selected items is no longer available.")

        variant = None
        price = food_item.price
        unit_price_label = food_item.unit_price_label
        if variant_id:
            variant_query = FoodVariant.objects.filter(pk=variant_id, food_item=food_item, active=True)
            if lock_rows:
                variant_query = variant_query.select_for_update()
            variant = variant_query.first()
            if not variant:
                if skip_unavailable:
                    warnings.append("Unavailable product sizes were removed from your cart.")
                    continue
                raise ValueError("One of the selected sizes is no longer available.")
            price = variant.price
            unit_price_label = variant.unit_price_label
        minimum_quantity = variant.minimum_quantity if variant else food_item.minimum_quantity
        if quantity < minimum_quantity:
            if adjust_minimum:
                quantity = minimum_quantity
                warnings.append(f"{food_item.name} quantity was updated to its minimum order quantity ({minimum_quantity}).")
            else:
                raise ValueError(f"{food_item.name} has a minimum order quantity of {minimum_quantity}.")

        subtotal = price * quantity
        total += subtotal
        items.append({
            "key": f"{food_item.pk}:{variant.pk if variant else 'base'}",
            "food_item_id": food_item.pk,
            "variant_id": variant.pk if variant else None,
            "name": food_item.name,
            "variant_name": variant.name if variant else "",
            "image_url": food_item.image.url if food_item.image else "",
            "category_name": food_item.category.name,
            "unit_price_label": unit_price_label,
            "minimum_quantity": minimum_quantity,
            "price": str(price),
            "quantity": quantity,
            "subtotal": str(subtotal),
        })
    return items, total, warnings


def cart(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body or b"{}")
            items, total, warnings = _resolve_cart_items(payload.get("cart"), adjust_minimum=True, skip_unavailable=True)
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, ValueError) as error:
            message = str(error) or "The cart data is invalid."
            return JsonResponse({"error": message}, status=400)

        request.session["cart"] = [
            {"food_item_id": item["food_item_id"], "variant_id": item["variant_id"], "quantity": item["quantity"]}
            for item in items
        ]
        return JsonResponse({"items": items, "total": str(total), "warnings": warnings})

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])

    try:
        items, total, warnings = _resolve_cart_items(request.session.get("cart", []), adjust_minimum=True, skip_unavailable=True)
    except ValueError:
        items, total = [], Decimal("0")
        warnings = []
        request.session["cart"] = []
    else:
        request.session["cart"] = [
            {"food_item_id": item["food_item_id"], "variant_id": item["variant_id"], "quantity": item["quantity"]}
            for item in items
        ]
    return render(request, "cart.html", {
        "cart_items": items,
        "cart_total": total,
        "cart_warnings": warnings,
        "cart_snapshot": {"items": items, "total": str(total)},
    })


def order(request):
    if not request.session.get("checkout_token"):
        request.session["checkout_token"] = str(uuid.uuid4())

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data["submission_token"]
            existing_order = Order.objects.filter(submission_token=token).first()
            if existing_order:
                if not existing_order.customer_email_sent or not existing_order.admin_email_sent:
                    try:
                        send_order_notifications(existing_order)
                    except Exception:
                        logger.exception("Order notification retry failed for %s", existing_order.order_number)
                request.session["last_order_id"] = existing_order.pk
                request.session["last_order_created_at"] = existing_order.created_at.isoformat()
                request.session.pop("checkout_token", None)
                request.session.pop("cart", None)
                return redirect("kitchen:order_success")

            if str(token) != request.session.get("checkout_token"):
                form.add_error(None, "Your checkout session expired. Please review your cart and try again.")
            else:
                try:
                    submitted_cart = json.loads(form.cleaned_data.get("cart_data") or "[]")
                    resolved_items, total, _ = _resolve_cart_items(submitted_cart)
                    if not resolved_items:
                        raise ValueError("Add at least one food item before submitting.")
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                    form.add_error("cart_data", str(error) or "The order list contains invalid data.")
                if not form.errors:
                    try:
                        with transaction.atomic():
                            resolved_items, total, _ = _resolve_cart_items(submitted_cart, lock_rows=True)
                            if not resolved_items:
                                raise ValueError("Add at least one food item before submitting.")
                            new_order = form.save(commit=False)
                            new_order.submission_token = token
                            new_order.total_amount = total
                            new_order.status = "pending"
                            new_order.save()
                            new_order.order_number = f"RK-{timezone.localdate():%Y%m%d}-{new_order.pk:03d}"
                            new_order.save(update_fields=("order_number", "updated_at"))
                            OrderItem.objects.bulk_create([
                                OrderItem(
                                    order=new_order,
                                    food_item=FoodItem.objects.get(pk=item["food_item_id"]),
                                    variant=FoodVariant.objects.filter(pk=item["variant_id"]).first() if item["variant_id"] else None,
                                    product_name=item["name"],
                                    variant_name_snapshot=item["variant_name"],
                                    quantity=item["quantity"],
                                    price=Decimal(item["price"]),
                                    subtotal=Decimal(item["subtotal"]),
                                )
                                for item in resolved_items
                            ])
                    except ValueError as error:
                        form.add_error("cart_data", str(error))
                    except IntegrityError:
                        new_order = Order.objects.filter(submission_token=token).first()
                        if not new_order:
                            raise

                    if not form.errors and (not new_order.customer_email_sent or not new_order.admin_email_sent):
                        try:
                            send_order_notifications(new_order)
                        except Exception:
                            logger.exception("Order notification processing failed for %s", new_order.order_number)
                            new_order.email_error = "Email notification processing failed. Please retry from Django Admin."
                            new_order.save(update_fields=("email_error", "updated_at"))
                    if not form.errors:
                        request.session["last_order_id"] = new_order.pk
                        request.session["last_order_created_at"] = new_order.created_at.isoformat()
                        request.session.pop("checkout_token", None)
                        request.session.pop("cart", None)
                        return redirect("kitchen:order_success")
    else:
        form = OrderForm(initial={"submission_token": request.session["checkout_token"]})
    try:
        checkout_items, checkout_total, checkout_warnings = _resolve_cart_items(
            request.session.get("cart", []), adjust_minimum=True, skip_unavailable=True
        )
    except ValueError:
        checkout_items, checkout_total = [], Decimal("0")
        checkout_warnings = []
        request.session["cart"] = []
    else:
        request.session["cart"] = [
            {"food_item_id": item["food_item_id"], "variant_id": item["variant_id"], "quantity": item["quantity"]}
            for item in checkout_items
        ]
    return render(request, "order.html", {
        "form": form,
        "checkout_items": checkout_items,
        "checkout_total": checkout_total,
        "checkout_warnings": checkout_warnings,
    })


def order_success(request):
    pk = request.session.get("last_order_id")
    created_at = request.session.get("last_order_created_at")
    if not pk or not created_at:
        return redirect("kitchen:order")
    try:
        if timezone.now() - datetime.fromisoformat(created_at) > timedelta(hours=1):
            request.session.pop("last_order_id", None)
            request.session.pop("last_order_created_at", None)
            return redirect("kitchen:order")
    except ValueError:
        return redirect("kitchen:order")
    order = get_object_or_404(Order.objects.prefetch_related("items__food_item", "items__variant"), pk=pk)
    return render(request, "order_success.html", {
        "order": order,
        "whatsapp_url": build_order_whatsapp_url(order),
    })
