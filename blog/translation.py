from modeltranslation.translator import TranslationOptions, register

from .models import Post


@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ("title", "excerpt", "body", "cta_label",
              "meta_title", "meta_description")
