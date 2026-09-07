from django.conf import settings
from django.urls import translate_url
from django.utils import translation

from .models import SiteSettings


def seo(request):
    """Expose the SiteSettings singleton, the canonical URL, and the language
    switcher (this same page in every configured language) to every template."""
    current = translation.get_language()
    languages = []
    try:
        here = request.get_full_path()
    except Exception:
        here = "/"
    for code, name in settings.LANGUAGES:
        try:
            url = translate_url(here, code)
        except Exception:
            url = here
        languages.append({
            "code": code,
            "name": name,
            "url": url,
            "active": code == current,
        })
    return {
        "site": SiteSettings.load(),
        "canonical_url": request.build_absolute_uri(request.path),
        "languages": languages,
        "current_language": current,
    }
