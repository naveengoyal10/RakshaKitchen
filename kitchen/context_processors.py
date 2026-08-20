import os
import re

from .models import WebsiteSettings


def website_settings(request):
    settings = WebsiteSettings.objects.first()
    phone = os.getenv("RAKSHA_PHONE", "+91 93051 26262").strip()
    email = os.getenv("RAKSHA_EMAIL", "raksha.shady@gmail.com").strip()
    raw_number = os.getenv("RAKSHA_WHATSAPP", "919305126262").strip()
    if settings:
        phone = settings.phone.strip() or phone
        email = settings.email.strip() or email
        raw_number = settings.whatsapp_number.strip() or raw_number
    return {
        "site_settings": settings,
        "contact_phone": phone,
        "contact_email": email,
        "whatsapp_number": re.sub(r"\D", "", raw_number) or "919305126262",
    }
