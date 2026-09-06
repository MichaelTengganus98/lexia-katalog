from django.urls import path
from .views import page, all_catalog

app_name = "katalog"

urlpatterns = [
    path('<int:id>/<slug:slug>', page, name="category"),
    path('', all_catalog, name="all-catalog")
]
