from django.contrib import admin
from .models import Item
# Register your models here.


class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "Jenis", "model_code", "feature_rank", "favorite", "availability", "noindex")
    list_editable = ("feature_rank",)
    list_filter = ("Jenis", "favorite", "availability", "noindex")
    search_fields = ("name", "model_code", "description")
    autocomplete_fields = ("replacement",)
    readonly_fields = ("dateTime", "updated")
    fieldsets = (
        (None, {
            "fields": ("Jenis", "name", "model_code", "brand"),
        }),
        ("Tampil di beranda", {
            "description": "Bagian \"Produk unggulan\" di beranda. Isi urutan 1-5 "
                           "(1 = kartu besar). \"Favorite\" dipakai sebagai cadangan "
                           "bila slot 1-5 belum terisi penuh.",
            "fields": ("feature_rank", "favorite"),
        }),
        ("Harga & ketersediaan", {
            "fields": ("price", "price_on_request", "availability", "replacement"),
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
