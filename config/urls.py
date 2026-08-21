from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from kitchen.sitemaps import KitchenSitemap

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("kitchen.urls")),
    path(
        "google8e50f1393451d06.html",
        TemplateView.as_view(
            template_name="google8e50f1393451d06.html",
            content_type="text/html",
        ),
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"kitchen": KitchenSitemap}},
    ),
]

if settings.DEBUG or settings.VERCEL:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )