from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from item.models import Item
from page.models import Category


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        return ["home", "about", "katalog:all-catalog"]

    def location(self, name):
        return reverse(name)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Category.objects.filter(noindex=False)

    def lastmod(self, obj):
        return obj.updated


class ItemSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        return Item.objects.filter(noindex=False)

    def lastmod(self, obj):
        return obj.updated


sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "items": ItemSitemap,
}
