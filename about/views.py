from django.shortcuts import render

from seo.jsonld import breadcrumb, graph, local_business
from seo.models import SiteSettings

# Create your views here.


def about(request):
    site = SiteSettings.load()
    crumbs = [("Beranda", "/"), ("Hubungi Kami", None)]
    return render(request, 'about/contact.html', {
        'page_title': 'Hubungi Kami',
        'page_description': ('Hubungi Lexia Machinery — distributor mesin percetakan & finishing '
                             'di Medan. Telepon, WhatsApp, alamat, dan lokasi peta.'),
        'page_jsonld': graph(request, local_business(request, site),
                             breadcrumb(request, crumbs)),
    })
