from django.db import models


class SeoModel(models.Model):
    """Reusable per-object SEO fields. Every field is optional and falls back to
    a sensible default in the template, so adding this to a model never forces
    editors to fill anything in."""

    meta_title = models.CharField(
        "Meta title (SEO)", max_length=70, blank=True,
        help_text="Judul di Google & saat link dibagikan. Kosongkan untuk memakai nama halaman. "
                  "Ideal 50-60 karakter.",
    )
    meta_description = models.CharField(
        "Meta description (SEO)", max_length=180, blank=True,
        help_text="Ringkasan di hasil pencarian Google. Kosongkan untuk memakai ringkasan otomatis. "
                  "Ideal 150-160 karakter.",
    )
    og_image = models.ImageField(
        "Gambar share (OG image)", upload_to="seo/", blank=True, null=True,
        help_text="Tampil saat link dibagikan di WhatsApp/Facebook. Ukuran ideal 1200x630 px. "
                  "Kosongkan untuk memakai foto utama.",
    )
    noindex = models.BooleanField(
        "Sembunyikan dari Google (noindex)", default=False,
        help_text="Centang agar halaman ini tidak muncul di hasil pencarian.",
    )
    updated = models.DateTimeField("Terakhir diperbarui", auto_now=True)

    class Meta:
        abstract = True


class SiteSettings(models.Model):
    """Single-row model holding site-wide SEO / organisation data used across
    every page (meta defaults, structured data, contact info, analytics)."""

    site_name = models.CharField(max_length=120, default="Lexia Machinery")
    tagline = models.CharField(
        max_length=200, blank=True,
        default="Distributor mesin percetakan & finishing",
    )
    default_meta_description = models.CharField(
        max_length=200, blank=True,
        help_text="Dipakai pada halaman yang tidak punya meta description sendiri.",
    )
    default_og_image = models.ImageField(
        upload_to="seo/", blank=True, null=True,
        help_text="Gambar share default (1200x630).",
    )

    # Contact / LocalBusiness
    phone_primary = models.CharField(max_length=40, blank=True, default="(+62) 61 4154876")
    phone_secondary = models.CharField(max_length=40, blank=True, default="(+62) 61 4515028")
    whatsapp_number = models.CharField(
        max_length=32, blank=True, default="6285275103333",
        help_text="Format internasional tanpa tanda +, mis. 6285275103333.",
    )
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True, default="Jalan Mesjid No. 165")
    city = models.CharField(max_length=80, blank=True, default="Medan")
    postal_code = models.CharField(max_length=16, blank=True)
    region = models.CharField(max_length=80, blank=True, default="Sumatera Utara")
    country = models.CharField(max_length=2, blank=True, default="ID")
    latitude = models.CharField(max_length=32, blank=True)
    longitude = models.CharField(max_length=32, blank=True)
    opening_hours = models.CharField(
        max_length=120, blank=True, default="Mo-Sa 08:00-17:00",
        help_text="Format schema.org, mis. 'Mo-Sa 08:00-17:00'.",
    )

    # Social (used for Organization sameAs)
    facebook_url = models.URLField(blank=True, default="https://www.facebook.com/lexiamachinery.ind/")
    instagram_url = models.URLField(blank=True, default="https://instagram.com/lexiamachinery.ind")
    youtube_url = models.URLField(blank=True, default="https://www.youtube.com/user/JeffryAldiP")
    tokopedia_url = models.URLField(blank=True, default="https://www.tokopedia.com/lexiamachinery")

    # Verification / analytics
    google_site_verification = models.CharField(
        max_length=120, blank=True,
        help_text="Isi content dari tag verifikasi Google Search Console.",
    )
    bing_site_verification = models.CharField(max_length=120, blank=True)
    ga_measurement_id = models.CharField(
        max_length=40, blank=True, help_text="ID Google Analytics 4, mis. G-XXXXXXXXXX.",
    )

    class Meta:
        verbose_name = "Pengaturan Situs & SEO"
        verbose_name_plural = "Pengaturan Situs & SEO"

    def __str__(self):
        return "Pengaturan Situs & SEO"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
