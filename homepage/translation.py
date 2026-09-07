from modeltranslation.translator import TranslationOptions, register

from .models import Brochure


@register(Brochure)
class BrochureTranslationOptions(TranslationOptions):
    fields = ("title", "description")
