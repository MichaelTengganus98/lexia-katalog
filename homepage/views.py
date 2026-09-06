from django.shortcuts import render

from item.models import Item
from .models import Brochure


def home(request):
    fav = Item.objects.filter(favorite=True)

    # Featured strip: favourites first, then the newest items to fill the layout.
    featured = list(fav)
    if len(featured) < 5:
        fill = Item.objects.exclude(pk__in=[i.pk for i in featured]).order_by('-dateTime')
        featured += list(fill[:5 - len(featured)])
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
