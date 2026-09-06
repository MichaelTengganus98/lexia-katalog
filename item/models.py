from django.db import models
from page.models import Category
from django.utils.text import slugify
# Create your models here.


def name_upload(instance, filename):
    return "upload/image/{}/{}/{}".format(instance.Jenis.jenis, instance.name, filename)


class Item(models.Model):
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

    def __str__(self):
        return self.name + " (" + self.Jenis.jenis + ")"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Item, self).save(*args, **kwargs)

    class Meta:
        ordering = ['name']

