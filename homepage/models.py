from django.db import models

# Create your models here.


def name_upload(instance, filename):
    return "upload/image/{}/{}/{}".format("Brosur", "homepage", filename)


def file_upload(instance, filename):
    return "upload/brosur/{}".format(filename)


class Brochure(models.Model):
    title = models.CharField("Judul brosur", max_length=200, default="Brosur")
    picture = models.ImageField("Gambar sampul", upload_to=name_upload)
    file = models.FileField(
        "Berkas (PDF)", upload_to=file_upload, blank=True, null=True,
        help_text="Opsional. Berkas PDF yang bisa diunduh pengunjung.",
    )
    description = models.CharField("Deskripsi singkat", max_length=255, blank=True)
    order = models.PositiveIntegerField("Urutan", default=0)
    is_active = models.BooleanField("Tampilkan", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-updated"]
        verbose_name = "Brosur"
        verbose_name_plural = "Brosur"

    def __str__(self):
        return self.title

    @property
    def download_url(self):
        if self.file:
            return self.file.url
        if self.picture:
            return self.picture.url
        return ""
