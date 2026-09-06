from django.contrib import admin
from .models import Brochure
# Register your models here.


@admin.register(Brochure)
class BrochureAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "updated")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    fields = ("title", "description", "picture", "file", "order", "is_active")
