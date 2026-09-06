from django.test import TestCase
from django.test import Client
from django.urls import resolve
from .views import about
from django.test import override_settings
# Create your tests here.


class TestAbout(TestCase):
    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False, CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        })
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

    def test_about_url_is_exist(self):
        response = Client().get("/contact")
        self.assertEqual(response.status_code, 200)

    def test_about_func(self):
        found = resolve("/contact")
        self.assertEqual(found.func, about)

