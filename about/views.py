from django.shortcuts import redirect, render

from seo.jsonld import breadcrumb, graph, local_business
from seo.models import SiteSettings
from .forms import ContactForm


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def about(request):
    site = SiteSettings.load()
    crumbs = [("Beranda", "/"), ("Hubungi Kami", None)]

    sent = request.GET.get("sent") == "1"
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ip_address = _client_ip(request)
            msg.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
            msg.save()
            return redirect("%s?sent=1" % request.path)
    else:
        form = ContactForm()

    return render(request, 'about/contact.html', {
        'form': form,
        'sent': sent,
        'page_title': 'Hubungi Kami',
        'page_description': ('Hubungi Lexia Machinery — distributor mesin percetakan & finishing '
                             'di Medan. Telepon, WhatsApp, alamat, dan lokasi peta.'),
        'page_jsonld': graph(request, local_business(request, site),
                             breadcrumb(request, crumbs)),
    })
