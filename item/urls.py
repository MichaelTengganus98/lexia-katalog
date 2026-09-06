from django.urls import path
from .views import item
app_name = "item"

urlpatterns = [
    path('<int:id>/<slug:slug>', item, name="mesin")
]