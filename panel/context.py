def panel_badges(request):
    """Sidebar badge counts, only for panel pages served to staff."""
    if (request.path.startswith("/panel/")
            and getattr(request, "user", None) is not None
            and request.user.is_authenticated and request.user.is_staff):
        from django.utils import timezone

        from about.models import ContactMessage
        from blog.models import Post
        from item.models import Item
        from page.models import Category

        seo_issues = (
            Item.objects.filter(noindex=True).count()
            + Category.objects.filter(noindex=True).count()
            + Post.objects.filter(
                status=Post.PUBLISHED, noindex=True,
                published_at__lte=timezone.now()).count()
        )
        return {
            "new_message_count": ContactMessage.objects.filter(
                status=ContactMessage.STATUS_NEW).count(),
            "seo_issue_count": seo_issues,
        }
    return {}
