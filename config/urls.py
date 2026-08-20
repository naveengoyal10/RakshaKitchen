from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from kitchen.sitemaps import KitchenSitemap

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("kitchen.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": {"kitchen": KitchenSitemap}}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
