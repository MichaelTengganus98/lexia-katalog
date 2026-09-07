from functools import wraps

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from about.models import ContactMessage
from blog.models import Post
from homepage.models import Brochure
from item.models import Item
from page.models import Category
from seo.models import SiteSettings

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
