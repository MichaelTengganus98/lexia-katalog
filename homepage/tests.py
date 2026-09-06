from django.test import TestCase
from django.test import Client
from django.urls import resolve
from .views import home
from django.test import override_settings
# Create your tests here.


class TestHomepage(TestCase):
    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False, CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        })
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

    def test_homepage_url_is_exist(self):
        response = Client().get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_func(self):
        found = resolve('/')
        self.assertEqual(found.func, home)
