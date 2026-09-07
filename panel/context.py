def panel_badges(request):
    """Sidebar badge counts, only for panel pages served to staff."""
    if (request.path.startswith("/panel/")
            and getattr(request, "user", None) is not None
            and request.user.is_authenticated and request.user.is_staff):
        from about.models import ContactMessage
        return {
            "new_message_count": ContactMessage.objects.filter(
                status=ContactMessage.STATUS_NEW).count(),
        }
    return {}
