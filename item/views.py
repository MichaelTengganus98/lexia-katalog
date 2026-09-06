from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Item
from page.models import Category
import re
# Create your views here.


@require_GET
def item(request, id, slug):
    item = get_object_or_404(Item, pk=id)
    if item.slug != slug:
        raise Http404
    specification = item.specification
    specDict = {}
    for line in specification.split("\r\n"):
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
    return render(request, 'item/product-detail.html', {
        'barang': item,
        'spec': specDict,
        'related': related_items,
    })
