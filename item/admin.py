from django.contrib import admin
from .models import Item
# Register your models here.


class ItemAdmin(admin.ModelAdmin):
    exclude = ('slug',)


admin.site.register(Item, ItemAdmin)