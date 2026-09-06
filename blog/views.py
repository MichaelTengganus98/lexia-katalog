from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from seo.jsonld import blog_posting, breadcrumb, graph
from .models import Post


def post_list(request):
    posts = Post.published.all()
    paginator = Paginator(posts, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "blog/list.html", {
        "posts": page_obj,
        "page_title": "Blog — Tips & Panduan Mesin Percetakan",
        "page_description": ("Artikel, tips, dan panduan seputar mesin percetakan dan finishing "
                             "dari Lexia Machinery."),
        "page_jsonld": graph(request, breadcrumb(request, [("Beranda", "/"), ("Blog", None)])),
    })


def post_detail(request, slug):
    qs = Post.objects.all() if request.user.is_staff else Post.published.all()
    post = get_object_or_404(qs, slug=slug)

    page_image = ""
    if post.og_image:
        page_image = request.build_absolute_uri(post.og_image.url)
    elif post.cover_image:
        page_image = request.build_absolute_uri(post.cover_image.url)

    crumbs = [("Beranda", "/"), ("Blog", "/blog/"), (post.title, None)]
    related_posts = Post.published.exclude(pk=post.pk)
    if post.related_category_id:
        same = related_posts.filter(related_category_id=post.related_category_id)
        related_posts = same or related_posts
    related_posts = related_posts[:3]

    return render(request, "blog/detail.html", {
        "post": post,
        "related_posts": related_posts,
        "page_title": post.seo_title,
        "page_description": post.seo_description,
        "page_image": page_image,
        "page_type": "article",
        "page_noindex": post.noindex or not post.is_live,
        "page_jsonld": graph(request, blog_posting(request, post),
                             breadcrumb(request, crumbs)),
    })
