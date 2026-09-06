import re

from django.shortcuts import render

from item.models import Item
from page.models import Category
from .models import Brochure


def _spec_pairs(text, limit=2):
    """Turn an Item.specification blob ("Label : value" per line) into a short
    list of (label, value) tuples for the homepage product cards."""
    pairs = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*(.+?)\s*:\s*(.+?)\s*$", line)
        if m:
            pairs.append((m.group(1), m.group(2)))
        if len(pairs) >= limit:
            break
    return pairs


def home(request):
    items = Item.objects.order_by('-dateTime')[:4]
    fav = Item.objects.filter(favorite=True)
    brosur = Brochure.objects.all()

    categories = Category.objects.all()

    # Featured strip: favourites first, then the newest items to fill the layout.
    featured = list(fav)
    if len(featured) < 5:
        fill = Item.objects.exclude(
            pk__in=[i.pk for i in featured]
        ).order_by('-dateTime')
        featured += list(fill[:5 - len(featured)])
    featured = featured[:5]
    for it in featured:
        it.spec_pairs = _spec_pairs(it.specification)

    return render(request, 'homepage/homepage.html', {
        'related': items,
        'favorites': fav,
        'brosur': brosur,
        'categories': categories,
        'featured': featured,
        'hero_item': featured[0] if featured else None,
        'item_count': Item.objects.count(),
    })
