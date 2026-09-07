from django import forms
from django.utils.text import slugify

from blog.models import Post
from item.models import Item
from page.models import Category

PICTURE_FIELDS = ["picture%d" % n for n in range(1, 11)]


class ProductForm(forms.ModelForm):
    FEATURE_CHOICES = [
        ("", "Tidak ditampilkan di beranda"),
        ("1", "#1 — Kartu besar (hero)"),
        ("2", "#2"),
        ("3", "#3"),
        ("4", "#4"),
        ("5", "#5"),
    ]

    feature_rank = forms.ChoiceField(
        choices=FEATURE_CHOICES, required=False, label="Prioritas unggulan",
    )

    class Meta:
        model = Item
        fields = [
            "name", "Jenis", "model_code", "summary", "description",
            *PICTURE_FIELDS, "urlVideo", "specification",
            "availability", "replacement", "feature_rank",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Contoh: Mesin Potong Kertas Hydraulic 5310"}),
            "model_code": forms.TextInput(attrs={"placeholder": "Contoh: 5310"}),
            "summary": forms.Textarea(attrs={"rows": 2, "placeholder": "1–2 kalimat yang muncul di bawah nama produk pada halaman detail."}),
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Deskripsi lengkap produk untuk bagian \"Deskripsi\"."}),
            "urlVideo": forms.TextInput(attrs={"placeholder": "https://www.youtube.com/watch?v=..."}),
            "specification": forms.Textarea(attrs={"rows": 5, "class": "spec-raw"}),
            "availability": forms.RadioSelect(),
        }
        labels = {
            "name": "Nama produk", "Jenis": "Kategori", "model_code": "Kode / SKU model",
            "summary": "Ringkasan singkat", "description": "Deskripsi lengkap",
            "urlVideo": "Tautan YouTube", "specification": "Spesifikasi teknis",
            "availability": "Ketersediaan",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Jenis"].queryset = Category.objects.all()
        self.fields["Jenis"].empty_label = "Pilih kategori"
        self.fields["description"].required = False
        self.fields["summary"].required = False
        self.fields["replacement"].queryset = Item.objects.exclude(
            pk=self.instance.pk) if self.instance.pk else Item.objects.all()
        self.fields["replacement"].empty_label = "— tidak ada —"
        self.fields["replacement"].label = "Produk pengganti"
        for name in PICTURE_FIELDS:
            self.fields[name].required = False
        self.fields["picture1"].label = "Foto Utama"
        for n in range(2, 11):
            self.fields["picture%d" % n].label = "Foto Tambahan %d" % n
        self.fields["picture1"].required = not bool(self.instance.pk and self.instance.picture1)
        if self.instance.pk and self.instance.feature_rank:
            self.initial["feature_rank"] = str(self.instance.feature_rank)

    def clean_feature_rank(self):
        v = self.cleaned_data.get("feature_rank")
        return int(v) if v else None


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            "title", "slug", "tag", "excerpt", "cover_image", "body",
            "related_category", "cta_label", "cta_url",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Contoh: Cara Memilih Mesin Laminating untuk Usaha Percetakan"}),
            "slug": forms.TextInput(attrs={"placeholder": "otomatis-dari-judul"}),
            "excerpt": forms.Textarea(attrs={"rows": 2, "placeholder": "1–2 kalimat ringkasan artikel (tampil di kartu)."}),
            "body": forms.Textarea(attrs={"class": "editor-body", "placeholder": "Tulis isi artikel di sini…"}),
            "cta_label": forms.TextInput(attrs={"placeholder": "Contoh: Lihat Katalog Laminating"}),
            "cta_url": forms.TextInput(attrs={"placeholder": "/katalog/ atau https://…"}),
        }
        labels = {
            "title": "Judul artikel", "slug": "Slug URL", "tag": "Tag artikel",
            "excerpt": "Ringkasan", "cover_image": "Foto sampul", "body": "Isi artikel",
            "related_category": "Kategori produk terkait",
            "cta_label": "Teks tombol akhir artikel", "cta_url": "Tautan tombol akhir artikel",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["excerpt"].required = False
        self.fields["related_category"].queryset = Category.objects.all()
        self.fields["related_category"].empty_label = "— tidak ada —"

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        if not slug:
            slug = slugify(self.cleaned_data.get("title", ""))[:220]
        qs = Post.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Slug ini sudah dipakai artikel lain.")
        return slug
