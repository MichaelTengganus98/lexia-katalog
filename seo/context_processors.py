from .models import SiteSettings


def seo(request):
    """Expose the SiteSettings singleton and a query-stripped canonical URL to
    every template."""
    return {
        "site": SiteSettings.load(),
        "canonical_url": request.build_absolute_uri(request.path),
    }
