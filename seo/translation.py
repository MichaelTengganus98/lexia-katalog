from modeltranslation.translator import TranslationOptions, register

from .models import SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "tagline", "default_meta_description",
        "home_kicker", "home_headline", "home_lead",
        "about_headline", "about_body",
        "contact_intro",
    )
