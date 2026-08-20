import re
from urllib.parse import quote

from .models import WebsiteSettings


DEFAULT_WHATSAPP_NUMBER = "9305126262"


def _site_settings():
    return WebsiteSettings.objects.first()


def _items_text(items_summary):
    if not items_summary:
        return "To be discussed"
    lines = []
    for item in items_summary.replace(", ", "\n").splitlines():
        item = re.sub(r"\s*\((\d+)\)$", r" x \1", item.strip())
        lines.append(item)
    return "\n".join(lines)


def build_whatsapp_order_message(inquiry):
    settings = _site_settings()
    business_name = settings.business_name if settings else "Raksha Kitchen"
    estimated_total = f"₹{inquiry.estimated_total:,.2f}" if inquiry.estimated_total is not None else "To be confirmed"
    preferred_date = inquiry.event_date.strftime("%d %b %Y") if inquiry.event_date else "Not specified"
    preferred_time = inquiry.preferred_time.strftime("%I:%M %p") if inquiry.preferred_time else "Not specified"
    fulfillment = inquiry.get_fulfillment_method_display() if inquiry.fulfillment_method else "Not specified"
    return "\n".join([
        f"Hello {business_name},",
        "I would like to place an order.",
        "",
        "Items:",
        _items_text(inquiry.items_summary),
        "",
        f"Estimated Total: {estimated_total}",
        "",
        f"Name: {inquiry.name}",
        f"Mobile: {inquiry.phone}",
        f"Preferred Date: {preferred_date}",
        f"Delivery/Pickup: {fulfillment} at {preferred_time}",
        f"Address: {inquiry.address}",
        f"Instructions: {inquiry.message or 'None'}",
    ])


def build_whatsapp_order_url(inquiry):
    settings = _site_settings()
    phone = settings.whatsapp_number if settings and settings.whatsapp_number else DEFAULT_WHATSAPP_NUMBER
    phone = re.sub(r"\D", "", phone)
    return f"https://wa.me/{phone}?text={quote(build_whatsapp_order_message(inquiry), safe='')}"


def build_order_whatsapp_message(order):
    settings = _site_settings()
    business_name = settings.business_name if settings else "Raksha Kitchen"
    lines = [
        f"Hello {business_name},",
        "I would like to place an order.",
        "",
        f"Order: {order.order_number}",
        "Items:",
    ]
    for item in order.items.all():
        label = f"{item.food_item.name} - {item.variant.name}" if item.variant else item.food_item.name
        lines.append(f"{label} x {item.quantity}")
    lines.extend([
        "",
        f"Estimated Total: ₹{order.total_amount:,.2f}",
        "",
        f"Name: {order.customer_name}",
        f"Mobile: {order.mobile}",
        f"Preferred Date: {order.preferred_date.strftime('%d %b %Y') if order.preferred_date else 'Not specified'}",
        f"Preferred Time: {order.preferred_time.strftime('%I:%M %p') if order.preferred_time else 'Not specified'}",
        f"Delivery/Pickup: {order.get_order_type_display()}",
        f"Address: {order.address}",
        f"Instructions: {order.notes or 'None'}",
    ])
    return "\n".join(lines)


def build_order_whatsapp_url(order):
    settings = _site_settings()
    phone = settings.whatsapp_number if settings and settings.whatsapp_number else DEFAULT_WHATSAPP_NUMBER
    phone = re.sub(r"\D", "", phone)
    return f"https://wa.me/{phone}?text={quote(build_order_whatsapp_message(order), safe='')}"
