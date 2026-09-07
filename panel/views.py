from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from about.models import ContactMessage
from blog.models import Post
from item.models import Item
from page.models import Category

from .forms import PostForm, ProductForm


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
