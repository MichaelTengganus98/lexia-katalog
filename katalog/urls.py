"""katalog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from homepage.views import home
from about.views import about, tentang
from seo.sitemaps import sitemaps

urlpatterns = [
    path('panel/', include('panel.urls', namespace="panel")),
    path('admin/', admin.site.urls),
    path('mesin/', include('item.urls', namespace="item")),
    path('katalog/', include('page.urls', namespace="katalog")),
    path('search/', include('search.urls', namespace="search")),
    path('blog/', include('blog.urls', namespace="blog")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
    path('', home, name='home'),
    path('tentang', tentang, name="tentang"),
    path('contact', about, name="about"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
