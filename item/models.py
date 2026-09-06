from django.db import models
from django.urls import reverse
from django.utils.text import slugify, Truncator

from page.models import Category
from seo.models import SeoModel
# Create your models here.


def name_upload(instance, filename):
    return "upload/image/{}/{}/{}".format(instance.Jenis.jenis, instance.name, filename)


AVAILABILITY_CHOICES = [
    ("InStock", "Tersedia / siap kirim"),
    ("PreOrder", "Pre-order"),
    ("OutOfStock", "Stok habis"),
    ("Discontinued", "Tidak diproduksi lagi"),
]


class Item(SeoModel):
    Jenis = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField("Nama barang", max_length=300, unique=True)
    favorite = models.BooleanField("Favorite", blank=True, default=False)
    description = models.TextField("Deskripsi barang", blank=True, null=True)
    picture1 = models.ImageField("Foto barang Utama", upload_to=name_upload, blank=False)
    picture2 = models.ImageField("Foto barang 2", upload_to=name_upload, blank=True, null=True)
    picture3 = models.ImageField("Foto barang 3", upload_to=name_upload, blank=True, null=True)
    picture4 = models.ImageField("Foto barang 4", upload_to=name_upload, blank=True, null=True)
    picture5 = models.ImageField("Foto barang 5", upload_to=name_upload, blank=True, null=True)
    picture6 = models.ImageField("Foto barang 6", upload_to=name_upload, blank=True, null=True)
    picture7 = models.ImageField("Foto barang 7", upload_to=name_upload, blank=True, null=True)
    picture8 = models.ImageField("Foto barang 8", upload_to=name_upload, blank=True, null=True)
    picture9 = models.ImageField("Foto barang 9", upload_to=name_upload, blank=True, null=True)
    picture10 = models.ImageField("Foto barang 10", upload_to=name_upload, blank=True, null=True)
    urlVideo = models.URLField("Link Video", blank=True, null=True)
    specification = models.TextField("Specification input: (Input) Name: specification", blank=True, null=True)
    dateTime = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField()

    # --- SEO / catalogue metadata -------------------------------------------
    model_code = models.CharField(
        "Kode / tipe model", max_length=60, blank=True,
        help_text="mis. 4606Z, 50R. Dipakai sebagai SKU/MPN pada data terstruktur.",
    )
    brand = models.CharField("Merek", max_length=80, blank=True, default="Lexia")
    summary = models.CharField(
        "Ringkasan singkat", max_length=300, blank=True,
        help_text="1-2 kalimat untuk kartu produk & meta description. "
                  "Kosongkan untuk memakai potongan deskripsi otomatis.",
    )
    price = models.DecimalField(
        "Harga (Rp)", max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Kosongkan bila harga hanya lewat penawaran.",
    )
    price_on_request = models.BooleanField("Harga hubungi kami", default=True)
    availability = models.CharField(
        "Ketersediaan", max_length=20, choices=AVAILABILITY_CHOICES, default="InStock",
    )

    def __str__(self):
        return self.name + " (" + self.Jenis.jenis + ")"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Item, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name']

    # --- helpers ----------------------------------------------------------
    def get_absolute_url(self):
        return reverse("item:mesin", kwargs={"id": self.id, "slug": self.slug})

    @property
    def images(self):
        out = []
        for n in range(1, 11):
            f = getattr(self, "picture%d" % n, None)
            if f:
                out.append(f)
        return out

    @property
    def seo_title(self):
        return self.meta_title or "%s — Harga & Spesifikasi" % self.name

    @property
    def seo_description(self):
        if self.meta_description:
            return self.meta_description
        if self.summary:
            return self.summary
        if self.description:
            return Truncator(self.description).chars(155)
        return "%s dari Lexia Machinery. Hubungi kami untuk harga dan informasi." % self.name
