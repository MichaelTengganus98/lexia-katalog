from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("produk/", views.product_list, name="product_list"),
    path("produk/urutan/", views.product_reorder, name="product_reorder"),
    path("produk/tambah/", views.product_form, name="product_create"),
    path("produk/<int:pk>/", views.product_form, name="product_edit"),
    path("produk/<int:pk>/hapus/", views.product_delete, name="product_delete"),

    path("blog/", views.post_list, name="post_list"),
    path("blog/tulis/", views.post_form, name="post_create"),
    path("blog/<int:pk>/", views.post_form, name="post_edit"),
    path("blog/<int:pk>/hapus/", views.post_delete, name="post_delete"),
]
