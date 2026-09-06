from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from item.models import Item
# Create your views here.


@require_GET
def search(request):
    q = (request.GET.get('mesin') or '').strip()
    listItem = Item.objects.filter(name__icontains=q) if q else Item.objects.none()
    paginator = Paginator(listItem, 12)
    p = request.GET.get('page')
    itemsPage = paginator.get_page(p)
    notFound = '' if listItem.count() else "tidak ditemukan"
    judul = ("Pencarian: %s %s" % (q, notFound)).strip() if q else "Pencarian"
    return render(request, 'page/katalog.html', {
        'item': itemsPage,
        'judul': judul,
        'query': q,
        'page_title': judul,
        'page_description': "Hasil pencarian mesin di katalog Lexia Machinery.",
        'page_noindex': True,
    })


@require_POST
def searchPost(request):
    q = request.POST['mesin']
    listres = list(Item.objects.filter(name__icontains=q).values_list("name", flat=True)[:4])
    return JsonResponse({'list': listres})
