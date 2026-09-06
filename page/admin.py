from django.contrib import admin
from .models import Category
# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("jenis", "noindex")
    search_fields = ("jenis",)
    readonly_fields = ("updated",)
    fieldsets = (
        (None, {
            "fields": ("jenis", "intro"),
        }),
        ("SEO", {
            "description": "Semua opsional. Kosongkan untuk memakai nilai otomatis.",
            "fields": ("meta_title", "meta_description", "og_image", "noindex"),
        }),
        ("Sistem", {
            "classes": ("collapse",),
            "fields": ("updated",),
        }),
    )


admin.site.register(Category, CategoryAdmin)
