"""katalog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.views.generic import TemplateView

from homepage.views import home
from about.views import about, tentang
from seo.sitemaps import sitemaps

# Language-neutral (no /en/ prefix): admin, staff panel, machine-readable.
urlpatterns = [
    path('panel/', include('panel.urls', namespace="panel")),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # set_language endpoint
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
]

# Public pages: Indonesian at "/", English at "/en/".
urlpatterns += i18n_patterns(
    path('mesin/', include('item.urls', namespace="item")),
    path('katalog/', include('page.urls', namespace="katalog")),
    path('search/', include('search.urls', namespace="search")),
    path('blog/', include('blog.urls', namespace="blog")),
    path('', home, name='home'),
    path('tentang', tentang, name="tentang"),
    path('contact', about, name="about"),
    prefix_default_language=False,
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
