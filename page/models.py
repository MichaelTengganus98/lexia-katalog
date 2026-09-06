from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from seo.models import SeoModel
# Create your models here.


class Category(SeoModel):
    jenis = models.CharField("Jenis", max_length=300)
    slug = models.SlugField()
    intro = models.TextField(
        "Teks pengantar kategori", blank=True,
        help_text="1-2 paragraf yang tampil di atas daftar produk. Konten unik di sini "
                  "sangat membantu peringkat kategori ini di Google.",
    )

    def __str__(self):
        return self.jenis

    def save(self, *args, **kwargs):
        self.slug = slugify(self.jenis)
        super(Category, self).save(*args, **kwargs)

    class Meta:
        ordering = ['jenis']
        verbose_name_plural = "Categories"

    def get_absolute_url(self):
        return reverse("katalog:category", kwargs={"id": self.id, "slug": self.slug})

    @property
    def seo_title(self):
        return self.meta_title or "Jual %s" % self.jenis

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        if self.intro:
            from django.utils.text import Truncator
            return Truncator(self.intro).chars(155)
        return ("Daftar %s dari Lexia Machinery, distributor mesin percetakan & finishing "
                "di Medan. Stok siap kirim." % self.jenis)
