from django.shortcuts import render

# Create your views here.


def about(request):
    return render(request, 'about/contact.html', {
        'page_title': 'Hubungi Kami',
        'page_description': ('Hubungi Lexia Machinery — distributor mesin percetakan & finishing '
                             'di Medan. Telepon, WhatsApp, alamat, dan lokasi peta.'),
    })
