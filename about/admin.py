from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "whatsapp", "category", "status", "created")
    list_filter = ("status", "category", "created")
    list_editable = ("status",)
    search_fields = ("name", "whatsapp", "email", "message")
    date_hierarchy = "created"
    readonly_fields = ("name", "whatsapp", "email", "category", "message",
                       "created", "updated", "ip_address", "user_agent")
    fieldsets = (
        ("Pesan dari pengunjung", {
            "fields": ("name", "whatsapp", "email", "category", "message"),
        }),
        ("Tindak lanjut", {
            "fields": ("status", "handled_note"),
        }),
        ("Sistem", {
            "classes": ("collapse",),
            "fields": ("created", "updated", "ip_address", "user_agent"),
        }),
    )

    def has_add_permission(self, request):
        return False
