from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path

from kitchen.sitemaps import KitchenSitemap


def google_verification(request):
    return HttpResponse(
        "google-site-verification: google8e50f1393451d06.html",
        content_type="text/html",
    )


urlpatterns = [
    path("admin/", admin.site.urls),

    # Google Search Console verification
    path(
        "google8e50f1393451d06.html",
        google_verification,
    ),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"kitchen": KitchenSitemap}},
    ),

    path("", include("kitchen.urls")),
]


if settings.DEBUG or settings.VERCEL:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )