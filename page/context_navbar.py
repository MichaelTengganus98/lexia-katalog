from .models import Category


def menu_mesin(context):
    link = Category.objects.all()
    return {
        'link_menu': link
    }
