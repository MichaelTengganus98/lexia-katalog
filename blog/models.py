from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator

from seo.models import SeoModel


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (super().get_queryset()
                .filter(status=Post.PUBLISHED, published_at__lte=timezone.now()))


class Post(SeoModel):
    DRAFT = "draft"
    PUBLISHED = "published"
    STATUS_CHOICES = [(DRAFT, "Draf"), (PUBLISHED, "Terbit")]

    TAG_CHOICES = [
        ("panduan", "Panduan Membeli"),
        ("perbandingan", "Perbandingan"),
        ("perawatan", "Perawatan"),
        ("tips", "Tips & Wawasan"),
        ("berita", "Berita"),
    ]

    title = models.CharField("Judul", max_length=200)
    tag = models.CharField(
        "Tag artikel", max_length=20, choices=TAG_CHOICES, default="tips",
        help_text="Label editorial yang tampil di kartu artikel (mis. \"Panduan Membeli\").",
    )
    slug = models.SlugField("Slug URL", max_length=220, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    published_at = models.DateTimeField(
        "Tanggal terbit", null=True, blank=True,
        help_text="Diisi otomatis saat status diubah ke Terbit bila masih kosong.",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="posts",
    )
    cover_image = models.ImageField("Gambar sampul", upload_to="blog/", blank=True, null=True)
    excerpt = models.CharField(
        "Ringkasan", max_length=300, blank=True,
        help_text="Tampil di daftar artikel & sebagai meta description bila kosong.",
    )
    body = models.TextField(
        "Isi artikel",
        help_text="Boleh berisi HTML (h2, h3, p, ul, a, img, blockquote, ...).",
    )
    related_category = models.ForeignKey(
        "page.Category", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="posts", verbose_name="Kategori produk terkait",
        help_text="Menautkan artikel ke satu kategori mesin (untuk internal link).",
    )
    cta_label = models.CharField(
        "Teks tombol akhir artikel", max_length=80, blank=True,
        help_text="Kosongkan untuk memakai tombol otomatis dari kategori terkait.",
    )
    cta_url = models.CharField(
        "Tautan tombol akhir artikel", max_length=300, blank=True,
        help_text="Path internal (mis. /katalog/) atau URL lengkap (https://...).",
    )
    created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-published_at", "-created"]
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    @property
    def is_live(self):
        return self.status == self.PUBLISHED and self.published_at and self.published_at <= timezone.now()

    @property
    def reading_time(self):
        words = len(strip_tags(self.body).split())
        return max(1, round(words / 200))

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        if self.excerpt:
            return self.excerpt
        return Truncator(strip_tags(self.body)).chars(155)
