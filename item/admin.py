from django.contrib import admin
from .models import Item
# Register your models here.


class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "Jenis", "model_code", "favorite", "availability", "noindex")
    list_filter = ("Jenis", "favorite", "availability", "noindex")
    search_fields = ("name", "model_code", "description")
    readonly_fields = ("dateTime", "updated")
    fieldsets = (
        (None, {
            "fields": ("Jenis", "name", "model_code", "brand", "favorite"),
        }),
        ("Harga & ketersediaan", {
            "fields": ("price", "price_on_request", "availability"),
        }),
        ("Konten", {
            "fields": ("summary", "description", "specification", "urlVideo"),
        }),
        ("Foto", {
            "fields": (
                "picture1", "picture2", "picture3", "picture4", "picture5",
                "picture6", "picture7", "picture8", "picture9", "picture10",
            ),
        }),
        ("SEO", {
            "description": "Semua opsional. Kosongkan untuk memakai nilai otomatis dari nama & deskripsi.",
            "fields": ("meta_title", "meta_description", "og_image", "noindex"),
        }),
        ("Sistem", {
            "classes": ("collapse",),
            "fields": ("dateTime", "updated"),
        }),
    )


admin.site.register(Item, ItemAdmin)
