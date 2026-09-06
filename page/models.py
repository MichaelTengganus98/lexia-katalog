from django.db import models
from django.utils.text import slugify
# Create your models here.


class Category(models.Model):
    jenis = models.CharField("Jenis", max_length=300)
    slug = models.SlugField()

    def __str__(self):
        return self.jenis

    def save(self, *args, **kwargs):
        self.slug = slugify(self.jenis)
        super(Category, self).save(*args, **kwargs)

    class Meta:
        ordering = ['jenis']
        verbose_name_plural = "Categories"
