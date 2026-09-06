import re

from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from page.models import Category
from .models import Item
# Create your views here.


@require_GET
def item(request, id, slug):
    item = get_object_or_404(Item, pk=id)
    if item.slug != slug:
        raise Http404
    specDict = {}
    for line in (item.specification or "").split("\r\n"):
        try:
            found = re.search('(.*): (.*)', line)
            specDict[found.group(1)] = found.group(2)
        except AttributeError:
            pass
    related = get_object_or_404(Category, jenis=item.Jenis)
    related_items = related.item_set.exclude(pk=item.pk)
    if related_items.count() >= 4:
        related_items = related_items[:4]
    else:
        related_items = None

    page_image = ""
    if item.og_image:
        page_image = request.build_absolute_uri(item.og_image.url)
    elif item.picture1:
        page_image = request.build_absolute_uri(item.picture1.url)

    return render(request, 'item/product-detail.html', {
        'barang': item,
        'spec': specDict,
        'related': related_items,
        'page_title': item.seo_title,
        'page_description': item.seo_description,
        'page_image': page_image,
        'page_type': 'product',
        'page_noindex': item.noindex,
    })
