from django.test import TestCase
from django.test import Client
from django.urls import resolve
from page.models import Category
from .models import Item
from .views import item

from django.test import override_settings
# Create your tests here.


class TestItem(TestCase):
    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False, CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        })
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

    def test_item_is_exist(self):
        kategori = Category.objects.create(jenis="test")
        item = Item.objects.create(Jenis=kategori, name="test", description="testDes",
                                   specification="Nama: ini\nJarak: test", picture1="../media/local/1.png")
        response = Client().get('/mesin/1/test')
        self.assertEqual(response.status_code, 200)

    def test_item_using_func(self):
        kategori = Category.objects.create(jenis="test")
        Item.objects.create(Jenis=kategori, name="test", description="testDes",
                            specification="Nama: ini\nJarak: test")
        found = resolve('/mesin/1/test')
        self.assertEqual(found.func, item)
