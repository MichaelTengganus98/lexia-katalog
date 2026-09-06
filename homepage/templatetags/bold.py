from django import template

register = template.Library()


def bold(text):
    return text.replace('**', '<strong>').replace('*/*', '</strong>')


register.filter('bold', bold)