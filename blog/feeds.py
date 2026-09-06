from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator

from .models import Post


class LatestPostsFeed(Feed):
    title = "Lexia Machinery — Blog"
    description = "Artikel & panduan seputar mesin percetakan dan finishing."
    link = "/blog/"

    def items(self):
        return Post.published.all()[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or Truncator(strip_tags(item.body)).chars(240)

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at

    def feed_url(self):
        return reverse("blog:feed")
