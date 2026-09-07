from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.utils.text import slugify

from about.models import ContactMessage
from blog.models import Post
from homepage.models import Brochure
from item.models import Item
from page.models import Category
from seo.models import SiteSettings

PICTURE_FIELDS = ["picture%d" % n for n in range(1, 11)]
User = get_user_model()


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


CTA_PAGES = [
    ("/", "Beranda"),
    ("/katalog/", "Katalog"),
    ("/blog/", "Blog"),
    ("/contact", "Hubungi Kami"),
]
_CTA_PAGE_PATHS = {p for p, _ in CTA_PAGES}


class PostForm(forms.ModelForm):
    CTA_TYPES = [
        ("", "— tidak ada (pakai tombol otomatis) —"),
        ("halaman", "Halaman Internal"),
        ("kategori", "Kategori Produk"),
        ("produk", "Halaman Produk"),
        ("url", "URL Eksternal"),
    ]

    cta_type = forms.ChoiceField(choices=CTA_TYPES, required=False, label="Tujuan tombol")
    cta_page = forms.ChoiceField(choices=CTA_PAGES, required=False, label="Pilih halaman")
    cta_category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, label="Pilih kategori",
        empty_label="Pilih kategori…")
    cta_product = forms.ModelChoiceField(
        queryset=Item.objects.all(), required=False, label="Pilih produk",
        empty_label="Pilih produk…")
    cta_external = forms.CharField(
        required=False, label="URL Eksternal",
        widget=forms.TextInput(attrs={"placeholder": "https://…"}))

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
            "cta_url": forms.HiddenInput(),
        }
        labels = {
            "title": "Judul artikel", "slug": "Slug URL", "tag": "Tag artikel",
            "excerpt": "Ringkasan", "cover_image": "Foto sampul", "body": "Isi artikel",
            "related_category": "Kategori produk terkait",
            "cta_label": "Teks tombol",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["excerpt"].required = False
        self.fields["cta_url"].required = False
        self.fields["related_category"].queryset = Category.objects.all()
        self.fields["related_category"].empty_label = "— tidak ada —"
        self._seed_cta_initial()

    def _seed_cta_initial(self):
        """Turn a stored cta_url back into (type, value) so the dropdowns
        show the current selection when editing."""
        url = (self.instance.cta_url or "").strip() if self.instance else ""
        if not url:
            return
        import re
        m = re.match(r"^/katalog/(\d+)/", url)
        if m:
            self.initial.setdefault("cta_type", "kategori")
            self.initial.setdefault("cta_category", m.group(1))
            return
        m = re.match(r"^/mesin/(\d+)/", url)
        if m:
            self.initial.setdefault("cta_type", "produk")
            self.initial.setdefault("cta_product", m.group(1))
            return
        if url in _CTA_PAGE_PATHS:
            self.initial.setdefault("cta_type", "halaman")
            self.initial.setdefault("cta_page", url)
            return
        self.initial.setdefault("cta_type", "url")
        self.initial.setdefault("cta_external", url)

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

    def clean(self):
        cleaned = super().clean()
        ctype = cleaned.get("cta_type") or ""
        label = (cleaned.get("cta_label") or "").strip()
        url = ""
        if ctype == "halaman":
            url = cleaned.get("cta_page") or ""
        elif ctype == "kategori":
            cat = cleaned.get("cta_category")
            if not cat:
                self.add_error("cta_category", "Pilih satu kategori.")
            else:
                url = cat.get_absolute_url()
        elif ctype == "produk":
            it = cleaned.get("cta_product")
            if not it:
                self.add_error("cta_product", "Pilih satu produk.")
            else:
                url = it.get_absolute_url()
        elif ctype == "url":
            ext = (cleaned.get("cta_external") or "").strip()
            if not (ext.startswith("http://") or ext.startswith("https://")):
                self.add_error("cta_external", "Masukkan URL lengkap yang diawali http:// atau https://")
            url = ext
        if ctype and not label:
            self.add_error("cta_label", "Isi teks tombol, atau pilih \"tidak ada\" untuk tombol otomatis.")
        cleaned["cta_url"] = url if ctype else ""
        if not ctype:
            cleaned["cta_label"] = ""
        self.instance.cta_url = cleaned["cta_url"]
        return cleaned


# --------------------------------------------------------------------------- #
#  Category & SEO
# --------------------------------------------------------------------------- #
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["jenis", "intro", "meta_title", "meta_description", "og_image", "noindex"]
        widgets = {
            "jenis": forms.TextInput(attrs={"placeholder": "Contoh: Mesin Potong Kertas"}),
            "intro": forms.Textarea(attrs={"rows": 5}),
            "meta_title": forms.TextInput(),
            "meta_description": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {"jenis": "Nama kategori"}


# --------------------------------------------------------------------------- #
#  Brochure
# --------------------------------------------------------------------------- #
class BrochureForm(forms.ModelForm):
    class Meta:
        model = Brochure
        fields = ["title", "description", "picture", "file", "order", "is_active"]
        widgets = {
            "title": forms.TextInput(),
            "description": forms.TextInput(),
            "order": forms.NumberInput(attrs={"min": 0}),
        }
        labels = {
            "title": "Judul brosur", "description": "Deskripsi singkat",
            "picture": "Gambar sampul", "file": "Berkas PDF (opsional)",
            "order": "Urutan tampil", "is_active": "Tampilkan di beranda",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["picture"].required = not bool(self.instance.pk and self.instance.picture)


# --------------------------------------------------------------------------- #
#  Incoming messages
# --------------------------------------------------------------------------- #
class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["status", "handled_note"]
        widgets = {"handled_note": forms.Textarea(attrs={"rows": 4})}
        labels = {"status": "Status tindak lanjut", "handled_note": "Catatan internal"}


# --------------------------------------------------------------------------- #
#  Site settings (singleton)
# --------------------------------------------------------------------------- #
class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = []
        widgets = {
            "default_meta_description": forms.Textarea(attrs={"rows": 2}),
        }


# --------------------------------------------------------------------------- #
#  Users
# --------------------------------------------------------------------------- #
class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    is_active = forms.BooleanField(label="Aktif", required=False, initial=True)
    is_staff = forms.BooleanField(label="Akses panel admin (staff)", required=False, initial=True)
    is_superuser = forms.BooleanField(label="Superuser (akses penuh)", required=False, initial=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data["is_active"]
        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = self.cleaned_data["is_superuser"]
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "is_active", "is_staff", "is_superuser")
        labels = {
            "is_active": "Aktif", "is_staff": "Akses panel admin (staff)",
            "is_superuser": "Superuser (akses penuh)",
        }


class PanelSetPasswordForm(SetPasswordForm):
    """SetPasswordForm already takes `user` as its first positional arg."""
