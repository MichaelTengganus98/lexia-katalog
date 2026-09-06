from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identitas", {
            "fields": ("site_name", "tagline", "default_meta_description", "default_og_image"),
        }),
        ("Kontak & Lokasi (untuk data terstruktur / Google Maps)", {
            "fields": (
                "phone_primary", "phone_secondary", "whatsapp_number", "email",
                "address", "city", "postal_code", "region", "country",
                "latitude", "longitude", "opening_hours",
            ),
        }),
        ("Media Sosial", {
            "fields": ("facebook_url", "instagram_url", "youtube_url", "tokopedia_url"),
        }),
        ("Verifikasi & Analytics", {
            "fields": ("google_site_verification", "bing_site_verification", "ga_measurement_id"),
        }),
    )

    def has_add_permission(self, request):
        # single-row model
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
