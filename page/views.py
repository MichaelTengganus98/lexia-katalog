from django.shortcuts import render
from django.views.decorators.http import require_GET
from .models import Category
from item.models import Item
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import Http404


# Create your views here.


@require_GET
def page(request, id, slug):
    page = get_object_or_404(Category, pk=id)
    if page.slug != slug:
        raise Http404
    items = page.item_set.all()
    paginator = Paginator(items, 12)
    p = request.GET.get('page')
    itemsPage = paginator.get_page(p)
    return render(request, 'page/katalog.html', {'item': itemsPage, 'judul': page.jenis})


def all_catalog(request):
    page = Item.objects.all()
    if not len(page) > 0:
        raise Http404
    paginator = Paginator(page, 12)
    p = request.GET.get('page')
    items_page = paginator.get_page(p)
    return render(request, 'page/katalog.html', {'item': items_page, 'judul': 'Semua Mesin'})
