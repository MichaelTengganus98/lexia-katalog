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


class TransEmptyNoneMixin:
    """Store an empty translated field as NULL, never ''. modeltranslation keeps
    `unique=True` on `<field>_ind` / `<field>_en`; multiple NULLs are allowed but
    multiple '' are not, so a blank English name on two products would clash."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if (name.endswith("_ind") or name.endswith("_en")) and hasattr(field, "empty_value"):
                field.empty_value = None


class ProductForm(TransEmptyNoneMixin, forms.ModelForm):
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
            "name_ind", "name_en", "Jenis", "model_code",
            "summary_ind", "summary_en", "description_ind", "description_en",
            *PICTURE_FIELDS, "urlVideo",
            "specification_ind", "specification_en",
            "availability", "replacement", "feature_rank",
            "meta_title_ind", "meta_title_en",
            "meta_description_ind", "meta_description_en",
            "og_image", "noindex",
        ]
        widgets = {
            "name_ind": forms.TextInput(attrs={"placeholder": "Contoh: Mesin Potong Kertas Hydraulic 5310"}),
            "name_en": forms.TextInput(attrs={"placeholder": "e.g. Hydraulic Paper Cutting Machine 5310"}),
            "model_code": forms.TextInput(attrs={"placeholder": "Contoh: 5310"}),
            "summary_ind": forms.Textarea(attrs={"rows": 2}),
            "summary_en": forms.Textarea(attrs={"rows": 2}),
            "description_ind": forms.Textarea(attrs={"rows": 6}),
            "description_en": forms.Textarea(attrs={"rows": 6}),
            "urlVideo": forms.TextInput(attrs={"placeholder": "https://www.youtube.com/watch?v=..."}),
            "specification_ind": forms.Textarea(attrs={"rows": 5, "class": "spec-raw"}),
            "specification_en": forms.Textarea(attrs={"rows": 5}),
            "availability": forms.RadioSelect(),
            "meta_title_ind": forms.TextInput(),
            "meta_title_en": forms.TextInput(),
            "meta_description_ind": forms.Textarea(attrs={"rows": 2}),
            "meta_description_en": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "name_ind": "Nama produk", "name_en": "Product name (English)",
            "Jenis": "Kategori", "model_code": "Kode / SKU model",
            "summary_ind": "Ringkasan singkat", "summary_en": "Short summary (English)",
            "description_ind": "Deskripsi lengkap", "description_en": "Full description (English)",
            "urlVideo": "Tautan YouTube",
            "specification_ind": "Spesifikasi teknis", "specification_en": "Technical specs (English)",
            "availability": "Ketersediaan",
            "meta_title_ind": "Meta title", "meta_title_en": "Meta title (English)",
            "meta_description_ind": "Meta description", "meta_description_en": "Meta description (English)",
            "og_image": "Gambar share (OG image)", "noindex": "Sembunyikan dari Google (noindex)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Jenis"].queryset = Category.objects.all()
        self.fields["Jenis"].empty_label = "Pilih kategori"
        for f in ("summary_ind", "summary_en", "description_ind", "description_en",
                  "name_en", "specification_ind", "specification_en",
                  "meta_title_ind", "meta_title_en",
                  "meta_description_ind", "meta_description_en", "og_image", "noindex"):
            self.fields[f].required = False
        self.fields["name_ind"].required = True
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

    def _unique_name(self, value, field):
        v = (value or "").strip()
        if not v:
            return None
        qs = Item.objects.filter(**{field: v})
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Nama produk ini sudah dipakai produk lain.")
        return v

    def clean_name_ind(self):
        return self._unique_name(self.cleaned_data.get("name_ind"), "name_ind")

    def clean_name_en(self):
        return self._unique_name(self.cleaned_data.get("name_en"), "name_en")


CTA_PAGES = [
    ("/", "Beranda"),
    ("/katalog/", "Katalog"),
    ("/blog/", "Blog"),
    ("/contact", "Hubungi Kami"),
]
_CTA_PAGE_PATHS = {p for p, _ in CTA_PAGES}


class PostForm(TransEmptyNoneMixin, forms.ModelForm):
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
            "title_ind", "title_en", "slug", "tag",
            "excerpt_ind", "excerpt_en", "cover_image",
            "body_ind", "body_en",
            "related_category", "cta_label_ind", "cta_label_en", "cta_url",
            "meta_title_ind", "meta_title_en",
            "meta_description_ind", "meta_description_en",
            "og_image", "noindex",
        ]
        widgets = {
            "title_ind": forms.TextInput(attrs={"placeholder": "Contoh: Cara Memilih Mesin Laminating untuk Usaha Percetakan"}),
            "title_en": forms.TextInput(attrs={"placeholder": "e.g. How to Choose a Laminating Machine for Your Print Shop"}),
            "slug": forms.TextInput(attrs={"placeholder": "otomatis-dari-judul"}),
            "excerpt_ind": forms.Textarea(attrs={"rows": 2}),
            "excerpt_en": forms.Textarea(attrs={"rows": 2}),
            "body_ind": forms.Textarea(attrs={"class": "editor-body", "placeholder": "Tulis isi artikel di sini…"}),
            "body_en": forms.Textarea(attrs={"class": "editor-body", "placeholder": "Write the article body here…"}),
            "cta_label_ind": forms.TextInput(attrs={"placeholder": "Contoh: Lihat Katalog Laminating"}),
            "cta_label_en": forms.TextInput(attrs={"placeholder": "e.g. See the Laminating Catalog"}),
            "cta_url": forms.HiddenInput(),
            "meta_title_ind": forms.TextInput(),
            "meta_title_en": forms.TextInput(),
            "meta_description_ind": forms.Textarea(attrs={"rows": 2}),
            "meta_description_en": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "title_ind": "Judul artikel", "title_en": "Article title (English)",
            "slug": "Slug URL", "tag": "Tag artikel",
            "excerpt_ind": "Ringkasan", "excerpt_en": "Summary (English)",
            "cover_image": "Foto sampul",
            "body_ind": "Isi artikel", "body_en": "Article body (English)",
            "related_category": "Kategori produk terkait",
            "cta_label_ind": "Teks tombol", "cta_label_en": "Button text (English)",
            "meta_title_ind": "Meta title", "meta_title_en": "Meta title (English)",
            "meta_description_ind": "Meta description", "meta_description_en": "Meta description (English)",
            "og_image": "Gambar share (OG image)", "noindex": "Sembunyikan dari Google (noindex)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["cta_url"].required = False
        for f in ("title_en", "excerpt_ind", "excerpt_en", "body_en",
                  "cta_label_ind", "cta_label_en",
                  "meta_title_ind", "meta_title_en",
                  "meta_description_ind", "meta_description_en", "og_image", "noindex"):
            self.fields[f].required = False
        self.fields["title_ind"].required = True
        self.fields["body_ind"].required = True
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
            slug = slugify(self.cleaned_data.get("title_ind", ""))[:220]
        qs = Post.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Slug ini sudah dipakai artikel lain.")
        return slug

    def clean(self):
        cleaned = super().clean()
        ctype = cleaned.get("cta_type") or ""
        label = (cleaned.get("cta_label_ind") or "").strip()
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
            self.add_error("cta_label_ind", "Isi teks tombol, atau pilih \"tidak ada\" untuk tombol otomatis.")
        cleaned["cta_url"] = url if ctype else ""
        if not ctype:
            cleaned["cta_label_ind"] = ""
            cleaned["cta_label_en"] = ""
        self.instance.cta_url = cleaned["cta_url"]
        return cleaned


# --------------------------------------------------------------------------- #
#  Category & SEO
# --------------------------------------------------------------------------- #
class CategoryForm(TransEmptyNoneMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["jenis_ind", "jenis_en", "intro_ind", "intro_en",
                  "meta_title_ind", "meta_title_en",
                  "meta_description_ind", "meta_description_en",
                  "og_image", "noindex"]
        widgets = {
            "jenis_ind": forms.TextInput(attrs={"placeholder": "Contoh: Mesin Potong Kertas"}),
            "jenis_en": forms.TextInput(attrs={"placeholder": "e.g. Paper Cutting Machines"}),
            "intro_ind": forms.Textarea(attrs={"rows": 5}),
            "intro_en": forms.Textarea(attrs={"rows": 5}),
            "meta_title_ind": forms.TextInput(),
            "meta_title_en": forms.TextInput(),
            "meta_description_ind": forms.Textarea(attrs={"rows": 2}),
            "meta_description_en": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "jenis_ind": "Nama kategori", "jenis_en": "Category name (English)",
            "intro_ind": "Teks pengantar", "intro_en": "Intro text (English)",
            "meta_title_ind": "Meta title", "meta_title_en": "Meta title (English)",
            "meta_description_ind": "Meta description", "meta_description_en": "Meta description (English)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["jenis_ind"].required = True
        for f in ("jenis_en", "intro_ind", "intro_en", "meta_title_ind", "meta_title_en",
                  "meta_description_ind", "meta_description_en"):
            self.fields[f].required = False


# --------------------------------------------------------------------------- #
#  Brochure
# --------------------------------------------------------------------------- #
class BrochureForm(TransEmptyNoneMixin, forms.ModelForm):
    class Meta:
        model = Brochure
        fields = ["title_ind", "title_en", "description_ind", "description_en",
                  "picture", "file", "order", "is_active"]
        widgets = {
            "title_ind": forms.TextInput(),
            "title_en": forms.TextInput(),
            "description_ind": forms.TextInput(),
            "description_en": forms.TextInput(),
            "order": forms.NumberInput(attrs={"min": 0}),
        }
        labels = {
            "title_ind": "Judul brosur", "title_en": "Brochure title (English)",
            "description_ind": "Deskripsi singkat", "description_en": "Short description (English)",
            "picture": "Gambar sampul", "file": "Berkas PDF (opsional)",
            "order": "Urutan tampil", "is_active": "Tampilkan di beranda",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title_ind"].required = True
        for f in ("title_en", "description_ind", "description_en"):
            self.fields[f].required = False
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
_SS_TRANSLATED = ("tagline", "default_meta_description", "home_kicker", "home_headline",
                  "home_lead", "about_headline", "about_body", "contact_intro")


class SiteSettingsForm(TransEmptyNoneMixin, forms.ModelForm):
    class Meta:
        model = SiteSettings
        # keep only the per-language columns; the bare translated fields are
        # kept in sync by modeltranslation on model save.
        exclude = list(_SS_TRANSLATED)
        widgets = {
            "default_meta_description_ind": forms.Textarea(attrs={"rows": 2}),
            "default_meta_description_en": forms.Textarea(attrs={"rows": 2}),
            "home_lead_ind": forms.Textarea(attrs={"rows": 3}),
            "home_lead_en": forms.Textarea(attrs={"rows": 3}),
            "about_body_ind": forms.Textarea(attrs={"rows": 6}),
            "about_body_en": forms.Textarea(attrs={"rows": 6}),
            "contact_intro_ind": forms.Textarea(attrs={"rows": 3}),
            "contact_intro_en": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name.endswith("_en"):
                field.required = False


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
