import json
import urllib.parse
import urllib.request
from collections import Counter
from functools import wraps

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from about.models import ContactMessage
from blog.models import Post
from homepage.models import Brochure
from item.models import Item
from page.models import Category
from seo.models import SiteSettings

from . import seogen
from .forms import (BrochureForm, CategoryForm, ContactMessageForm, PanelSetPasswordForm,
                    PostForm, ProductForm, SiteSettingsForm, UserCreateForm, UserEditForm)

User = get_user_model()


def superuser_required(view):
    @wraps(view)
    @staff_member_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Butuh akses superuser.")
        return view(request, *args, **kwargs)
    return _wrapped


# --------------------------------------------------------------------------- #
#  Quick translate  (fill ID/EN content fields from the other language)
# --------------------------------------------------------------------------- #
# Keyless Google endpoints. clients5 keeps paragraph breaks and takes several
# `q=` params per request; translate.googleapis is the fallback when it 429s.
_GT_URL = "https://clients5.google.com/translate_a/t"
_GT_FALLBACK = "https://translate.googleapis.com/translate_a/single"
_GT_MAXQ = 5000         # cap on encoded query length per request
_GT_LANGS = {"id", "en"}
_GT_HEADERS = {"User-Agent": "Mozilla/5.0 (LexiaPanel quick-translate)"}


def _gt_get(url):
    req = urllib.request.Request(url, headers=_GT_HEADERS)
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gt_fallback_one(text, source, target):
    """translate.googleapis.com/single — one text, returns joined segments."""
    query = urllib.parse.urlencode({
        "client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text,
    })
    data = _gt_get(_GT_FALLBACK + "?" + query)
    return "".join(seg[0] for seg in (data[0] or []) if seg and seg[0])


def _gt_batch(texts, source, target):
    """clients5 — a list of texts in one request, order preserved."""
    query = urllib.parse.urlencode(
        [("client", "dict-chrome-ex"), ("sl", source), ("tl", target)]
        + [("q", t) for t in texts]
    )
    try:
        data = _gt_get(_GT_URL + "?" + query)
        out = []
        for item in data:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, list) and item:
                out.append(item[0])
            else:
                out.append("")
        if len(out) == len(texts):
            return out
    except Exception:
        pass
    return [_gt_fallback_one(t, source, target) for t in texts]


def _gt_long(text, source, target):
    """Split an oversized field on paragraph breaks, translate, rejoin."""
    parts, buf = [], ""
    for para in text.split("\n\n"):
        cand = (buf + "\n\n" + para) if buf else para
        if len(urllib.parse.quote(cand)) <= _GT_MAXQ:
            buf = cand
            continue
        if buf:
            parts.append(buf)
            buf = ""
        while len(urllib.parse.quote(para)) > _GT_MAXQ:
            cut = _GT_MAXQ // 3
            parts.append(para[:cut])
            para = para[cut:]
        buf = para
    if buf:
        parts.append(buf)
    return "\n\n".join(_gt_translate_many(parts, source, target))


def _gt_translate_many(texts, source, target):
    """Translate texts, batching short ones and handling long ones separately."""
    results = [""] * len(texts)
    pending, pending_idx, pending_len = [], [], 0

    def flush():
        if not pending:
            return
        for j, out in enumerate(_gt_batch(pending, source, target)):
            results[pending_idx[j]] = out
        del pending[:]
        del pending_idx[:]

    for i, raw in enumerate(texts):
        text = raw or ""
        enc = len(urllib.parse.quote(text))
        if enc > _GT_MAXQ:
            flush()
            pending_len = 0
            results[i] = _gt_long(text, source, target)
            continue
        if pending and pending_len + enc > _GT_MAXQ:
            flush()
            pending_len = 0
        pending.append(text)
        pending_idx.append(i)
        pending_len += enc
    flush()
    return results


@staff_member_required
@require_POST
def translate(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Permintaan tidak valid."}, status=400)

    source = payload.get("source")
    target = payload.get("target")
    texts = payload.get("q")
    if source not in _GT_LANGS or target not in _GT_LANGS or source == target \
            or not isinstance(texts, list):
        return JsonResponse({"error": "Parameter bahasa tidak valid."}, status=400)

    try:
        results = _gt_translate_many([str(t) for t in texts[:20]], source, target)
    except Exception:
        return JsonResponse(
            {"error": "Layanan terjemahan sedang sibuk. Coba lagi sebentar, atau isi manual."},
            status=502,
        )
    return JsonResponse({"translations": results})


# --------------------------------------------------------------------------- #
#  SEO recommendations  ("Isi dengan rekomendasi SEO" button)
# --------------------------------------------------------------------------- #
_SEO_MODELS = {"product": Item, "post": Post, "category": Category}


@staff_member_required
@require_POST
def seo_suggest(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Permintaan tidak valid."}, status=400)

    kind = payload.get("type")
    lang = payload.get("lang")
    if kind not in _SEO_MODELS or lang not in ("id", "en"):
        return JsonResponse({"error": "Parameter tidak valid."}, status=400)

    try:
        obj = _SEO_MODELS[kind].objects.get(pk=payload.get("id"))
    except (_SEO_MODELS[kind].DoesNotExist, ValueError, TypeError):
        return JsonResponse(
            {"error": "Simpan dulu sebelum memakai rekomendasi SEO."}, status=404)

    try:
        data = seogen.suggest(kind, obj, lang)
    except Exception:
        return JsonResponse({"error": "Tidak bisa membuat rekomendasi saat ini."}, status=500)
    return JsonResponse(data)


# --------------------------------------------------------------------------- #
#  SEO Health  (read-only audit of existing content)
# --------------------------------------------------------------------------- #
def _seo_row(label, url, external=False):
    return {"label": label, "url": url, "external": external}


def _seo_check(severity, label, offenders, hint):
    return {
        "severity": severity if offenders else "ok",
        "label": label,
        "count": len(offenders),
        "offenders": offenders[:40],
        "more": max(0, len(offenders) - 40),
        "hint": hint,
    }


@staff_member_required
def seo_health(request):
    def c(s):
        return (s or "").strip()

    sections = []

    # ---- Produk -------------------------------------------------------------
    items = list(Item.objects.select_related("Jenis").all())
    purl = lambda it: reverse("panel:product_edit", args=[it.pk])
    dup_title = Counter(c(it.meta_title).lower() for it in items if c(it.meta_title))
    sections.append({"name": "Produk", "total": len(items), "checks": [
        _seo_check("error", "Disembunyikan dari Google (noindex)",
                   [_seo_row(it.name, purl(it)) for it in items if it.noindex],
                   "Buka produk → kartu \"SEO & Pratinjau Berbagi\" → hilangkan centang "
                   "\"Sembunyikan dari Google\"."),
        _seo_check("warn", "Ringkasan pencarian lemah (tak ada ringkasan & deskripsi)",
                   [_seo_row(it.name, purl(it)) for it in items
                    if not (c(it.meta_description) or c(it.summary) or c(it.description))],
                   "Isi Ringkasan singkat / Deskripsi lengkap, atau klik "
                   "\"Isi dengan rekomendasi SEO\" di kartu SEO."),
        _seo_check("warn", "Tak ada gambar berbagi (OG image & foto utama kosong)",
                   [_seo_row(it.name, purl(it)) for it in items
                    if not it.og_image and not it.picture1],
                   "Unggah Foto Utama produk, atau OG image khusus di kartu SEO."),
        _seo_check("warn", "Judul SEO lebih dari 60 karakter (terpotong di Google)",
                   [_seo_row("%s — %d kar." % (it.name, len(it.seo_title)), purl(it))
                    for it in items if len(it.seo_title) > 60],
                   "Isi Meta title yang lebih pendek di kartu SEO."),
        _seo_check("warn", "Meta description lebih dari 160 karakter",
                   [_seo_row("%s — %d kar." % (it.name, len(it.seo_description)), purl(it))
                    for it in items if len(it.seo_description) > 160],
                   "Persingkat Meta description di kartu SEO."),
        _seo_check("warn", "Meta title sama dengan produk lain (duplikat)",
                   [_seo_row(it.name, purl(it)) for it in items
                    if c(it.meta_title) and dup_title[c(it.meta_title).lower()] > 1],
                   "Buat Meta title yang unik untuk tiap produk."),
        _seo_check("info", "Belum ada konten Bahasa Inggris (nama produk)",
                   [_seo_row(it.name, purl(it)) for it in items
                    if not c(getattr(it, "name_en", ""))],
                   "Isi kolom English di kartu Informasi Dasar, lalu pakai tombol terjemah."),
    ]})

    # ---- Kategori ---------------------------------------------------------
    cats = list(Category.objects.all())
    curl = lambda cat: reverse("panel:category_edit", args=[cat.pk])
    sections.append({"name": "Kategori", "total": len(cats), "checks": [
        _seo_check("error", "Disembunyikan dari Google (noindex)",
                   [_seo_row(cat.jenis, curl(cat)) for cat in cats if cat.noindex],
                   "Buka kategori → kartu SEO → hilangkan centang noindex."),
        _seo_check("warn", "Halaman kategori tipis (teks pengantar kosong)",
                   [_seo_row(cat.jenis, curl(cat)) for cat in cats if not c(cat.intro)],
                   "Tulis 1–2 paragraf pengantar — konten unik di sini sangat membantu "
                   "peringkat kategori di Google."),
        _seo_check("warn", "Meta description lebih dari 160 karakter",
                   [_seo_row("%s — %d kar." % (cat.jenis, len(cat.seo_description)), curl(cat))
                    for cat in cats if len(cat.seo_description) > 160],
                   "Persingkat Meta description di kartu SEO."),
        _seo_check("info", "Belum ada nama kategori Bahasa Inggris",
                   [_seo_row(cat.jenis, curl(cat)) for cat in cats
                    if not c(getattr(cat, "jenis_en", ""))],
                   "Isi kolom English pada nama kategori."),
    ]})

    # ---- Blog -----------------------------------------------------------
    posts = list(Post.objects.all())
    live = [p for p in posts if p.is_live]
    burl = lambda p: reverse("panel:post_edit", args=[p.pk])
    sections.append({"name": "Blog", "total": len(posts), "checks": [
        _seo_check("error", "Artikel terbit disembunyikan dari Google (noindex)",
                   [_seo_row(p.title, burl(p)) for p in live if p.noindex],
                   "Buka artikel → kartu SEO → hilangkan centang noindex."),
        _seo_check("warn", "Artikel terbit tanpa foto sampul",
                   [_seo_row(p.title, burl(p)) for p in live if not p.cover_image],
                   "Unggah Foto sampul — dipakai di kartu blog dan saat link dibagikan."),
        _seo_check("warn", "Judul SEO lebih dari 60 karakter",
                   [_seo_row("%s — %d kar." % (p.title, len(p.seo_title)), burl(p))
                    for p in live if len(p.seo_title) > 60],
                   "Isi Meta title yang lebih pendek di kartu SEO."),
        _seo_check("info", "Artikel terbit tanpa ringkasan (dibuat otomatis dari isi)",
                   [_seo_row(p.title, burl(p)) for p in live if not c(p.excerpt)],
                   "Isi Ringkasan untuk kontrol penuh atas teks di Google & kartu artikel."),
        _seo_check("info", "Belum ada judul artikel Bahasa Inggris",
                   [_seo_row(p.title, burl(p)) for p in live
                    if not c(getattr(p, "title_en", ""))],
                   "Isi kolom English pada judul, lalu terjemahkan isinya."),
    ]})

    # ---- Situs -----------------------------------------------------------
    site = SiteSettings.load()
    surl = reverse("panel:site_settings")
    missing = []
    if not c(site.google_site_verification):
        missing.append(_seo_row("Kode verifikasi Google Search Console", surl))
    if not site.default_og_image:
        missing.append(_seo_row("Gambar berbagi default (OG image)", surl))
    if not c(site.default_meta_description):
        missing.append(_seo_row("Meta description default situs", surl))
    if not c(site.ga_measurement_id):
        missing.append(_seo_row("ID Google Analytics 4", surl))
    if not c(site.email):
        missing.append(_seo_row("Email (dipakai di data terstruktur)", surl))
    if not (c(site.latitude) and c(site.longitude)):
        missing.append(_seo_row("Koordinat lokasi (latitude & longitude)", surl))
    sections.append({"name": "Situs & data terstruktur", "total": None, "checks": [
        _seo_check("warn", "Data SEO situs belum lengkap", missing,
                   "Lengkapi di Pengaturan Situs & SEO."),
    ]})

    # ---- Teknis --------------------------------------------------------
    sections.append({"name": "Teknis", "total": None, "checks": [{
        "severity": "info",
        "label": "Berkas teknis — buka untuk memastikan keduanya benar",
        "count": 0,
        "offenders": [_seo_row("sitemap.xml", "/sitemap.xml", True),
                      _seo_row("robots.txt", "/robots.txt", True)],
        "more": 0,
        "hint": "Daftarkan sitemap.xml di Google Search Console setelah verifikasi.",
    }]})

    errors = sum(ck["count"] for s in sections for ck in s["checks"] if ck["severity"] == "error")
    warnings = sum(ck["count"] for s in sections for ck in s["checks"] if ck["severity"] == "warn")

    return render(request, "panel/seo_health.html", {
        "section": "seo",
        "title": "SEO Health",
        "sections": sections,
        "errors": errors,
        "warnings": warnings,
        "live_posts": len(live),
    })


# --------------------------------------------------------------------------- #
#  Dashboard
# --------------------------------------------------------------------------- #
@staff_member_required
def dashboard(request):
    incomplete = Item.objects.filter(picture1="").count()
    new_messages = ContactMessage.objects.filter(status=ContactMessage.STATUS_NEW).count()
    stats = [
        ("Produk", Item.objects.count(), False),
        ("Kategori", Category.objects.count(), False),
        ("Artikel blog", Post.objects.count(), False),
        ("Pesan baru", new_messages, bool(new_messages)),
        ("Produk tanpa foto", incomplete, bool(incomplete)),
    ]
    return render(request, "panel/dashboard.html", {
        "section": "dashboard",
        "title": "Dashboard",
        "stats": stats,
        "recent_items": Item.objects.select_related("Jenis").order_by("-updated")[:8],
        "recent_messages": ContactMessage.objects.order_by("-created")[:6],
    })


# --------------------------------------------------------------------------- #
#  Products
# --------------------------------------------------------------------------- #
@staff_member_required
def product_list(request):
    items = Item.objects.select_related("Jenis", "replacement").all()
    featured = Item.objects.filter(feature_rank__isnull=False).order_by("feature_rank")
    return render(request, "panel/product_list.html", {
        "section": "produk",
        "title": "Produk",
        "items": items,
        "featured": featured,
    })


@staff_member_required
@require_POST
def product_reorder(request):
    ids = request.POST.getlist("order[]") or request.POST.getlist("order")
    with transaction.atomic():
        Item.objects.filter(feature_rank__isnull=False).update(feature_rank=None)
        for rank, pk in enumerate(ids[:5], start=1):
            Item.objects.filter(pk=pk).update(feature_rank=rank)
    return JsonResponse({"ok": True, "count": min(len(ids), 5)})


@staff_member_required
def product_form(request, pk=None):
    instance = get_object_or_404(Item, pk=pk) if pk else None
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Produk \"%s\" disimpan." % obj.name)
            return redirect("panel:product_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = ProductForm(instance=instance)
    return render(request, "panel/product_form.html", {
        "section": "produk",
        "title": "Edit Produk" if instance else "Tambah Produk",
        "form": form,
        "instance": instance,
        "picture_fields": ["picture%d" % n for n in range(1, 11)],
    })


@staff_member_required
@require_POST
def product_delete(request, pk):
    obj = get_object_or_404(Item, pk=pk)
    name = obj.name
    obj.delete()
    messages.success(request, "Produk \"%s\" dihapus." % name)
    return redirect("panel:product_list")


# --------------------------------------------------------------------------- #
#  Blog
# --------------------------------------------------------------------------- #
@staff_member_required
def post_list(request):
    posts = Post.objects.select_related("related_category", "author").all()
    return render(request, "panel/post_list.html", {
        "section": "blog",
        "title": "Blog",
        "posts": posts,
    })


@staff_member_required
def post_form(request, pk=None):
    instance = get_object_or_404(Post, pk=pk) if pk else None
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.author_id is None:
                obj.author = request.user
            if "save_draft" in request.POST:
                obj.status = Post.DRAFT
            else:
                obj.status = Post.PUBLISHED
                if obj.published_at is None:
                    obj.published_at = timezone.now()
            obj.save()
            messages.success(request, "Artikel \"%s\" disimpan." % obj.title)
            return redirect("panel:post_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = PostForm(instance=instance)
    return render(request, "panel/post_form.html", {
        "section": "blog",
        "title": "Edit Artikel" if instance else "Tulis Artikel",
        "form": form,
        "instance": instance,
    })


@staff_member_required
@require_POST
def post_delete(request, pk):
    obj = get_object_or_404(Post, pk=pk)
    title = obj.title
    obj.delete()
    messages.success(request, "Artikel \"%s\" dihapus." % title)
    return redirect("panel:post_list")


# --------------------------------------------------------------------------- #
#  Category & SEO
# --------------------------------------------------------------------------- #
@staff_member_required
def category_list(request):
    cats = Category.objects.all()
    return render(request, "panel/category_list.html", {
        "section": "kategori", "title": "Kategori & SEO", "cats": cats,
    })


@staff_member_required
def category_form(request, pk=None):
    instance = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Kategori \"%s\" disimpan." % obj.jenis)
            return redirect("panel:category_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = CategoryForm(instance=instance)
    return render(request, "panel/category_form.html", {
        "section": "kategori",
        "title": "Edit Kategori" if instance else "Tambah Kategori",
        "form": form, "instance": instance,
    })


@staff_member_required
@require_POST
def category_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    if obj.item_set.exists():
        messages.error(request, "Kategori \"%s\" masih dipakai %d produk — pindahkan produk itu dulu."
                       % (obj.jenis, obj.item_set.count()))
        return redirect("panel:category_edit", pk=pk)
    name = obj.jenis
    obj.delete()
    messages.success(request, "Kategori \"%s\" dihapus." % name)
    return redirect("panel:category_list")


# --------------------------------------------------------------------------- #
#  Brochures
# --------------------------------------------------------------------------- #
@staff_member_required
def brochure_list(request):
    return render(request, "panel/brochure_list.html", {
        "section": "brosur", "title": "Brosur",
        "brochures": Brochure.objects.all(),
    })


@staff_member_required
def brochure_form(request, pk=None):
    instance = get_object_or_404(Brochure, pk=pk) if pk else None
    if request.method == "POST":
        form = BrochureForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Brosur \"%s\" disimpan." % obj.title)
            return redirect("panel:brochure_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = BrochureForm(instance=instance)
    return render(request, "panel/brochure_form.html", {
        "section": "brosur",
        "title": "Edit Brosur" if instance else "Tambah Brosur",
        "form": form, "instance": instance,
    })


@staff_member_required
@require_POST
def brochure_delete(request, pk):
    obj = get_object_or_404(Brochure, pk=pk)
    title = obj.title
    obj.delete()
    messages.success(request, "Brosur \"%s\" dihapus." % title)
    return redirect("panel:brochure_list")


# --------------------------------------------------------------------------- #
#  Incoming messages
# --------------------------------------------------------------------------- #
@staff_member_required
def message_list(request):
    qs = ContactMessage.objects.select_related("category").all()
    status = request.GET.get("status") or ""
    if status:
        qs = qs.filter(status=status)
    return render(request, "panel/message_list.html", {
        "section": "pesan", "title": "Pesan Masuk",
        "messages_list": qs,
        "status_choices": ContactMessage.STATUS_CHOICES,
        "active_status": status,
        "new_count": ContactMessage.objects.filter(status=ContactMessage.STATUS_NEW).count(),
    })


@staff_member_required
def message_detail(request, pk):
    obj = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        form = ContactMessageForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Pesan dari %s diperbarui." % obj.name)
            return redirect("panel:message_list")
    else:
        if obj.status == ContactMessage.STATUS_NEW:
            ContactMessage.objects.filter(pk=obj.pk).update(status=ContactMessage.STATUS_READ)
            obj.refresh_from_db()
        form = ContactMessageForm(instance=obj)
    return render(request, "panel/message_form.html", {
        "section": "pesan", "title": "Pesan dari %s" % obj.name,
        "obj": obj, "form": form,
    })


@staff_member_required
@require_POST
def message_delete(request, pk):
    obj = get_object_or_404(ContactMessage, pk=pk)
    name = obj.name
    obj.delete()
    messages.success(request, "Pesan dari %s dihapus." % name)
    return redirect("panel:message_list")


# --------------------------------------------------------------------------- #
#  Site settings (singleton)
# --------------------------------------------------------------------------- #
@staff_member_required
def site_settings(request):
    obj = SiteSettings.load()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Pengaturan situs disimpan.")
            return redirect("panel:site_settings")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = SiteSettingsForm(instance=obj)
    # each entry: field name (language-neutral) or ("trans", base) for id/en pair
    groups = [
        ("Identitas", ["site_name", ("trans", "tagline"),
                       ("trans", "default_meta_description"), "default_og_image"]),
        ("Halaman: Beranda", [("trans", "home_kicker"), ("trans", "home_headline"),
                              ("trans", "home_lead")]),
        ("Halaman: Tentang Kami", [("trans", "about_headline"), ("trans", "about_body"),
                                   "about_image"]),
        ("Halaman: Hubungi Kami", [("trans", "contact_intro")]),
        ("Kontak & Lokasi", ["phone_primary", "phone_secondary", "whatsapp_number", "email",
                             "address", "city", "postal_code", "region", "country",
                             "latitude", "longitude", "opening_hours"]),
        ("Media Sosial", ["facebook_url", "instagram_url", "youtube_url", "tokopedia_url"]),
        ("Verifikasi & Analytics", ["google_site_verification", "bing_site_verification", "ga_measurement_id"]),
    ]
    def _bf(name):
        try:
            return form[name]
        except KeyError:
            return None

    resolved = []
    for heading, names in groups:
        items = []
        for n in names:
            if isinstance(n, tuple) and n[0] == "trans":
                items.append(("trans", _bf(n[1] + "_ind"), _bf(n[1] + "_en")))
            elif n in ("default_og_image", "about_image"):
                items.append(("image", _bf(n), None))
            else:
                items.append(("plain", _bf(n), None))
        has_trans = any(k == "trans" for k, _a, _b in items)
        resolved.append((heading, items, has_trans))

    return render(request, "panel/settings_form.html", {
        "section": "pengaturan", "title": "Pengaturan Situs & SEO",
        "form": form, "groups": resolved,
    })


# --------------------------------------------------------------------------- #
#  Users  (superuser only)
# --------------------------------------------------------------------------- #
@superuser_required
def user_list(request):
    return render(request, "panel/user_list.html", {
        "section": "pengguna", "title": "Pengguna",
        "users": User.objects.order_by("username"),
    })


@superuser_required
def user_form(request, pk=None):
    instance = get_object_or_404(User, pk=pk) if pk else None
    FormClass = UserEditForm if instance else UserCreateForm
    if request.method == "POST":
        form = FormClass(request.POST, instance=instance) if instance else FormClass(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Pengguna \"%s\" disimpan." % obj.username)
            return redirect("panel:user_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = FormClass(instance=instance) if instance else FormClass()
    return render(request, "panel/user_form.html", {
        "section": "pengguna",
        "title": "Edit Pengguna" if instance else "Tambah Pengguna",
        "form": form, "instance": instance, "is_self": instance == request.user,
    })


@superuser_required
def user_password(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = PanelSetPasswordForm(obj, request.POST)
        if form.is_valid():
            form.save()
            if obj == request.user:
                update_session_auth_hash(request, obj)
            messages.success(request, "Kata sandi untuk \"%s\" diperbarui." % obj.username)
            return redirect("panel:user_list")
        messages.error(request, "Periksa kembali isian yang ditandai merah.")
    else:
        form = PanelSetPasswordForm(obj)
    return render(request, "panel/user_password.html", {
        "section": "pengguna", "title": "Ubah Kata Sandi — %s" % obj.username,
        "form": form, "obj": obj,
    })


@superuser_required
@require_POST
def user_delete(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if obj == request.user:
        messages.error(request, "Anda tidak bisa menghapus akun Anda sendiri.")
        return redirect("panel:user_list")
    username = obj.username
    obj.delete()
    messages.success(request, "Pengguna \"%s\" dihapus." % username)
    return redirect("panel:user_list")
