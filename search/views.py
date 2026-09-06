from django.shortcuts import render
from item.models import Item
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
# Create your views here.


@require_GET
def search(request):
    q = request.GET.get('mesin')
    listItem = Item.objects.filter(name__icontains=q)
    paginator = Paginator(listItem, 12)
    p = request.GET.get('page')
    itemsPage = paginator.get_page(p)
    notFound=''
    if listItem.count() == 0:
        notFound = "tidak ditemukan"
    return render(request, 'page/katalog.html', {'item': itemsPage, 'judul': "Pencarian: " + q + " " + notFound})


@require_POST
def searchPost(request):
    q = request.POST['mesin']
    listres = list(Item.objects.filter(name__icontains=q).values_list("name", flat=True)[:4])
    return JsonResponse({'list': listres})
