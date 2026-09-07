import re

from django import forms

from page.models import Category
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "whatsapp", "email", "category", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama Anda"}),
            "whatsapp": forms.TextInput(attrs={"placeholder": "08xx-xxxx-xxxx"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@domain.com (opsional)"}),
            "message": forms.Textarea(attrs={
                "placeholder": "Ceritakan kebutuhan Anda…", "rows": 5,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["category"].required = False
        self.fields["category"].queryset = Category.objects.all()
        self.fields["category"].empty_label = "Pilih kategori mesin (opsional)"

    def clean_whatsapp(self):
        raw = (self.cleaned_data.get("whatsapp") or "").strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) < 8:
            raise forms.ValidationError("Masukkan nomor WhatsApp yang valid.")
        return raw

    def clean_message(self):
        msg = (self.cleaned_data.get("message") or "").strip()
        if len(msg) < 10:
            raise forms.ValidationError("Mohon tulis pesan minimal 10 karakter.")
        return msg
