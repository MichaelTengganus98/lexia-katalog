from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "tag", "status", "published_at", "author", "related_category")
    list_filter = ("status", "tag", "related_category", "author")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    autocomplete_fields = ()
    readonly_fields = ("created", "updated")
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "tag", "author", "related_category"),
        }),
        ("Konten", {
            "fields": ("cover_image", "excerpt", "body"),
        }),
        ("Terbit", {
            "fields": ("status", "published_at"),
        }),
        ("SEO", {
            "description": "Opsional. Kosongkan untuk memakai judul & ringkasan.",
            "fields": ("meta_title", "meta_description", "og_image", "noindex"),
        }),
        ("Sistem", {
            "classes": ("collapse",),
            "fields": ("created", "updated"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)
