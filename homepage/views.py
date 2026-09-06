from django.shortcuts import render
from item.models import Item
from .models import Brochure
# Create your views here.


def home(request):
    items = Item.objects.order_by('-dateTime')[:4]
    fav = Item.objects.filter(favorite=True)
    brosur = Brochure.objects.all()
    return render(request, 'homepage/homepage.html', {'related': items,
                                                      'favorites': fav,
                                                      'brosur': brosur})
