import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.contrib import messages

from .forms import CustomerInquiryForm, OrderForm
from .models import Category, CustomerInquiry, FoodItem, FoodVariant, Order, OrderItem
from .utils import build_order_whatsapp_url


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
    item = get_object_or_404(FoodItem, slug=slug, available=True)
    return render(request, "menu_detail.html", {"item": item})


def menu_pricing(request):
    items = FoodItem.objects.filter(available=True).values("id", "price", "unit_quantity", "unit")
    variants = FoodVariant.objects.filter(active=True, food_item__available=True).values("id", "price", "unit_quantity", "unit")
    return JsonResponse({
        "items": {
            str(item["id"]): {
                "price": str(item["price"]),
                "unit_quantity": item["unit_quantity"],
                "unit": item["unit"],
            }
            for item in items
        },
        "variants": {
            str(variant["id"]): {
                "price": str(variant["price"]),
                "unit_quantity": variant["unit_quantity"],
                "unit": variant["unit"],
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
    popular_items = FoodItem.objects.filter(available=True).order_by("-featured", "display_order", "name")[:6]
    return render(request, "bulk_orders.html", {"form": form, "popular_items": popular_items})


def contact(request):
    return render(request, "contact.html")


def robots(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n",
        content_type="text/plain",
    )


def order(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                cart = json.loads(form.cleaned_data.get("cart_data") or "[]")
            except json.JSONDecodeError:
                cart = None
            if not isinstance(cart, list) or not cart:
                form.add_error("cart_data", "Add at least one food item before submitting.")
            else:
                resolved_items = []
                total = Decimal("0")
                for cart_item in cart:
                    if not isinstance(cart_item, dict):
                        form.add_error("cart_data", "The order list contains invalid data.")
                        break
                    try:
                        food_item_id = int(cart_item.get("food_item_id")) if cart_item.get("food_item_id") else None
                        quantity = int(cart_item.get("quantity"))
                        variant_id = cart_item.get("variant_id")
                        variant_id = int(variant_id) if variant_id else None
                    except (TypeError, ValueError):
                        form.add_error("cart_data", "The order list contains invalid data.")
                        break
                    if not 1 <= quantity <= 999:
                        form.add_error("cart_data", "Each quantity must be between 1 and 999.")
                        break
                    food_item_query = {"pk": food_item_id} if food_item_id else {"name": cart_item.get("name", "")}
                    food_item = FoodItem.objects.filter(available=True, **food_item_query).first()
                    if not food_item:
                        form.add_error("cart_data", "One of the selected items is no longer available.")
                        break
                    variant = None
                    price = food_item.price
                    if variant_id:
                        variant = FoodVariant.objects.filter(pk=variant_id, food_item=food_item, active=True).first()
                        if not variant:
                            form.add_error("cart_data", "One of the selected sizes is no longer available.")
                            break
                        price = variant.price
                    subtotal = price * quantity
                    resolved_items.append((food_item, variant, quantity, price, subtotal))
                    total += subtotal
                if not form.errors:
                    with transaction.atomic():
                        new_order = form.save(commit=False)
                        new_order.total_amount = total
                        new_order.save()
                        OrderItem.objects.bulk_create([
                            OrderItem(order=new_order, food_item=item, variant=variant, quantity=quantity, price=price, subtotal=subtotal)
                            for item, variant, quantity, price, subtotal in resolved_items
                        ])
                    request.session["last_order_id"] = new_order.pk
                    request.session["last_order_created_at"] = timezone.now().isoformat()
                    return redirect("kitchen:order_success")
    else:
        form = OrderForm()
    return render(request, "order.html", {"form": form})


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
