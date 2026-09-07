from django.shortcuts import render

from item.models import Item
from .models import Brochure


def home(request):
    # Featured strip (homepage "Produk unggulan"): explicit feature_rank order
    # first, then favourites, then the newest items to fill the 5-slot layout.
    featured = list(Item.objects.filter(feature_rank__isnull=False).order_by('feature_rank'))

    def _fill(qs):
        seen = {i.pk for i in featured}
        for it in qs.exclude(pk__in=seen):
            if len(featured) >= 5:
                break
            featured.append(it)

    if len(featured) < 5:
        _fill(Item.objects.filter(favorite=True))
    if len(featured) < 5:
        _fill(Item.objects.order_by('-dateTime'))
    featured = featured[:5]

    return render(request, 'homepage/homepage.html', {
        'featured': featured,
        'hero_item': featured[0] if featured else None,
        'item_count': Item.objects.count(),
        'brochures': Brochure.objects.filter(is_active=True),
        'page_description': ('Distributor resmi mesin percetakan dan finishing di Medan & Jakarta — '
                            'mesin potong kertas, laminating, lem binding, perforasi, dan lainnya. '
                            'Stok siap kirim, konsultasi gratis.'),
    })
