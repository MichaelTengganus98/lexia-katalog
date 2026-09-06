from django.test import TestCase
from .models import Category
from .views import page
from django.test import Client
from django.urls import resolve
# Create your tests here.

from django.test import override_settings


class TestPage(TestCase):
    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False, CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        })
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

    def test_url_is_exist_based_on_model(self):
        Category.objects.create(jenis="test")
        response = Client().get('/katalog/1/test')
        self.assertEqual(response.status_code, 200)

    def test_page_func(self):
        Category.objects.create(jenis="test1")
        found = resolve('/katalog/1/test1')
        self.assertEqual(found.func, page)

