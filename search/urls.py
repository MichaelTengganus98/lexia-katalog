from django.urls import path
from .views import search, searchPost
app_name = "search"

urlpatterns = [
    path('', search, name="category"),
    path('post', searchPost, name="searchpost")
]