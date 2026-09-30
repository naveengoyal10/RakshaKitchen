import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _delivery_address(order):
    return "\n".join(part for part in (order.address, order.building_society, order.flat_number) if part)


def _contact_details():
    from .models import WebsiteSettings

    website = WebsiteSettings.objects.first()
    phone = (website.phone if website and website.phone else getattr(settings, "RAKSHA_PHONE", "")).strip()
    contact_email = (website.email if website and website.email else getattr(settings, "RAKSHA_EMAIL", "")).strip()
    return phone, contact_email


def _items_text(order):
    lines = []
    for item in order.items.all():
        name = item.product_name or item.food_item.name
        variant = item.variant_name_snapshot or (item.variant.name if item.variant_id else "")
        if variant:
            name = f"{name} — {variant}"
        lines.append(
            f"{name} × {item.quantity} | ₹{item.price} each | Subtotal ₹{item.subtotal}"
        )
    return "\n".join(lines)


def _send_email(subject, body, recipient, from_email):
    resend_api_key = getattr(settings, "RESEND_API_KEY", "").strip()
    if resend_api_key:
        sender = getattr(settings, "RESEND_FROM_EMAIL", "").strip()
        if not sender:
            raise RuntimeError("RESEND_FROM_EMAIL must be set to a sender address verified with Resend.")
        request = Request(
            "https://api.resend.com/emails",
            data=json.dumps({
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "text": body,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": f"raksha-order-email-{subject.rsplit('#', 1)[-1]}-{recipient}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"Resend returned HTTP {response.status}.")
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("id"):
                    raise RuntimeError("Resend did not return an email ID.")
                return
        except HTTPError as exc:
            provider_message = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"Resend HTTP {exc.code}: {provider_message}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not connect to Resend: {exc}") from exc

    if (
        settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
        and not settings.EMAIL_HOST
    ):
        raise RuntimeError("SMTP email is not configured; set EMAIL_HOST and SMTP credentials.")
    sent = send_mail(subject, body, from_email, [recipient], fail_silently=False)
    if sent != 1:
        raise RuntimeError("The email backend did not accept the message.")


def _common_order_text(order):
    phone, contact_email = _contact_details()
    created = timezone.localtime(order.created_at).strftime("%d %b %Y, %I:%M %p %Z")
    delivery = f"{order.preferred_date or 'Not specified'} at {order.preferred_time.strftime('%I:%M %p') if order.preferred_time else 'Not specified'}"
    return (
        f"Order ID: {order.order_number}\n"
        f"Customer: {order.customer_name}\n"
        f"Order date/time: {created}\n"
        f"Items:\n{_items_text(order)}\n\n"
        f"Total amount: ₹{order.total_amount}\n"
        f"Delivery date/time: {delivery}\n"
        f"Delivery address:\n{_delivery_address(order)}\n"
        f"Order status: {order.get_status_display()}\n\n"
        f"Raksha Kitchen contact: {phone or 'Please contact us by replying to this email'}"
        f"{f' | {contact_email}' if contact_email else ''}"
    )


def send_order_notifications(order):
    """Send any unsent order emails and persist delivery status without losing the order."""
    errors = []
    try:
        common_text = _common_order_text(order)
    except Exception as exc:
        logger.exception("Could not prepare order emails for %s", order.order_number)
        order.email_error = f"Email content could not be prepared: {exc}"
        order.save(update_fields=("email_error", "updated_at"))
        return False
    from_email = settings.DEFAULT_FROM_EMAIL

    if not order.customer_email_sent:
        if order.email:
            body = (
                f"Thank you for ordering from Raksha Kitchen, {order.customer_name}!\n\n"
                "Your order has been received. We will contact you to confirm availability and delivery.\n\n"
                f"{common_text}\n"
            )
            try:
                _send_email(
                    f"Raksha Kitchen — Order Confirmation #{order.order_number}",
                    body,
                    order.email,
                    from_email,
                )
                order.customer_email_sent = True
            except Exception as exc:  # Email errors must never roll back a saved order.
                logger.exception("Customer order email failed for %s", order.order_number)
                errors.append(f"Customer email: {exc}")
        else:
            errors.append("Customer email: no recipient address was provided.")

    if not order.admin_email_sent:
        admin_email = getattr(settings, "ADMIN_ORDER_EMAIL", "").strip()
        if admin_email:
            phone = order.mobile
            body = (
                f"New Raksha Kitchen order: {order.order_number}\n\n"
                f"{common_text}\n"
                f"Customer mobile: {phone}\n"
                f"Customer email: {order.email or 'Not provided'}\n"
                f"Customer notes: {order.notes or 'None'}\n"
            )
            try:
                _send_email(
                    f"New Raksha Kitchen Order — #{order.order_number}",
                    body,
                    admin_email,
                    from_email,
                )
                order.admin_email_sent = True
            except Exception as exc:  # Email errors must never roll back a saved order.
                logger.exception("Admin order email failed for %s", order.order_number)
                errors.append(f"Admin email: {exc}")
        else:
            logger.warning("Admin order email skipped for %s: ADMIN_ORDER_EMAIL is not configured", order.order_number)
            errors.append("Admin email: ADMIN_ORDER_EMAIL is not configured.")

    order.email_error = "\n".join(errors)
    order.save(update_fields=("customer_email_sent", "admin_email_sent", "email_error", "updated_at"))
    return not errors
