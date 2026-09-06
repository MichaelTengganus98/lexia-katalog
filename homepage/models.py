from django.db import models

# Create your models here.


def name_upload(instacne, filename):
    return "upload/image/{}/{}/{}".format("Brosur", "homepage", filename)


class Brochure(models.Model):
    picture = models.ImageField("Foto brosur", upload_to=name_upload)
