from django.db import models


class ContactMessage(models.Model):
    """A "Hubungi Kami" form submission. Read / triaged from the admin —
    editors update `status` and `handled_note`; the submitted fields are
    read-only there."""

    STATUS_NEW = "new"
    STATUS_READ = "read"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_NEW, "Baru"),
        (STATUS_READ, "Dibaca"),
        (STATUS_IN_PROGRESS, "Ditindaklanjuti"),
        (STATUS_DONE, "Selesai"),
        (STATUS_ARCHIVED, "Arsip"),
    ]

    name = models.CharField("Nama lengkap", max_length=120)
    whatsapp = models.CharField("No. WhatsApp", max_length=32)
    email = models.EmailField("Email", blank=True)
    category = models.ForeignKey(
        "page.Category", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="contact_messages", verbose_name="Mesin yang diminati",
    )
    message = models.TextField("Pesan")

    status = models.CharField(
        "Status", max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW,
    )
    handled_note = models.TextField(
        "Catatan internal", blank=True,
        help_text="Catatan tim — tidak tampil ke pengunjung.",
    )

    created = models.DateTimeField("Masuk pada", auto_now_add=True)
    updated = models.DateTimeField("Diperbarui", auto_now=True)

    # light spam / audit context (not shown in the form)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Pesan Masuk"
        verbose_name_plural = "Pesan Masuk (Hubungi Kami)"

    def __str__(self):
        return "%s — %s" % (self.name, self.created.strftime("%d %b %Y"))
