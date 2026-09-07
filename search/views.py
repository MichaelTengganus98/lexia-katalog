from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from item.models import Item


def _match(q):
    """Search both language columns (bare `name` follows the active language,
    which can miss rows whose translation is empty)."""
    return Q(name_ind__icontains=q) | Q(name_en__icontains=q)


@require_GET
def search(request):
    q = (request.GET.get('mesin') or '').strip()
    listItem = Item.objects.filter(_match(q)) if q else Item.objects.none()
    paginator = Paginator(listItem, 12)
    p = request.GET.get('page')
    itemsPage = paginator.get_page(p)
    notFound = '' if listItem.count() else _("tidak ditemukan")
    judul = ("%s: %s %s" % (_("Pencarian"), q, notFound)).strip() if q else _("Pencarian")
    return render(request, 'page/katalog.html', {
        'item': itemsPage,
        'judul': judul,
        'query': q,
        'page_title': judul,
        'page_description': _("Hasil pencarian mesin di katalog Lexia Machinery."),
        'page_noindex': True,
    })


@require_POST
def searchPost(request):
    q = request.POST['mesin']
    listres = list(Item.objects.filter(_match(q)).values_list("name", flat=True)[:4])
    return JsonResponse({'list': listres})
