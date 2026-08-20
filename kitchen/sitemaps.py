from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import FoodItem


class KitchenSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            "kitchen:home",
            "kitchen:about",
            "kitchen:menu",
            "kitchen:bulk_orders",
            "kitchen:contact",
            "kitchen:order",
        ] + list(FoodItem.objects.filter(available=True))

    def location(self, item):
        if isinstance(item, str):
            return reverse(item)
        return reverse("kitchen:menu_detail", kwargs={"slug": item.slug})

    def lastmod(self, item):
        if isinstance(item, FoodItem):
            return item.updated_at
        return None
