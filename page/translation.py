from modeltranslation.translator import TranslationOptions, register

from .models import Category


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("jenis", "intro", "meta_title", "meta_description")
