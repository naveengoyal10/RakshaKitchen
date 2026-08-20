import re

from .models import WebsiteSettings


def website_settings(request):
    settings = WebsiteSettings.objects.first()
    raw_number = settings.whatsapp_number if settings else ""
    return {
        "site_settings": settings,
        "whatsapp_number": re.sub(r"\D", "", raw_number) or "919876543210",
    }
