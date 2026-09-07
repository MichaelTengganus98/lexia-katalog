from django import template

register = template.Library()


@register.inclusion_tag("admin/_lexia_dashboard.html")
def lexia_dashboard():
    """Summary strip shown at the top of the admin dashboard — mirrors the
    'ringkasan cepat' panel from the design reference."""
    from item.models import Item
    from page.models import Category
    from blog.models import Post
    from about.models import ContactMessage

    incomplete = Item.objects.filter(picture1="").count()
    new_messages = ContactMessage.objects.filter(status=ContactMessage.STATUS_NEW).count()

    return {
        "stats": [
            ("Produk", Item.objects.count(), None),
            ("Kategori", Category.objects.count(), None),
            ("Artikel blog", Post.objects.count(), None),
            ("Pesan baru", new_messages, "attention" if new_messages else None),
            ("Produk tanpa foto", incomplete, "attention" if incomplete else None),
        ],
        "recent_items": Item.objects.order_by("-updated")[:8],
        "recent_messages": ContactMessage.objects.order_by("-created")[:5],
    }
