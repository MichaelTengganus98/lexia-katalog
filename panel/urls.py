from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("translate/", views.translate, name="translate"),
    path("seo-suggest/", views.seo_suggest, name="seo_suggest"),
    path("seo/", views.seo_health, name="seo_health"),

    path("produk/", views.product_list, name="product_list"),
    path("produk/urutan/", views.product_reorder, name="product_reorder"),
    path("produk/tambah/", views.product_form, name="product_create"),
    path("produk/<int:pk>/", views.product_form, name="product_edit"),
    path("produk/<int:pk>/hapus/", views.product_delete, name="product_delete"),

    path("blog/", views.post_list, name="post_list"),
    path("blog/tulis/", views.post_form, name="post_create"),
    path("blog/<int:pk>/", views.post_form, name="post_edit"),
    path("blog/<int:pk>/hapus/", views.post_delete, name="post_delete"),

    path("kategori/", views.category_list, name="category_list"),
    path("kategori/tambah/", views.category_form, name="category_create"),
    path("kategori/<int:pk>/", views.category_form, name="category_edit"),
    path("kategori/<int:pk>/hapus/", views.category_delete, name="category_delete"),

    path("brosur/", views.brochure_list, name="brochure_list"),
    path("brosur/tambah/", views.brochure_form, name="brochure_create"),
    path("brosur/<int:pk>/", views.brochure_form, name="brochure_edit"),
    path("brosur/<int:pk>/hapus/", views.brochure_delete, name="brochure_delete"),

    path("pesan/", views.message_list, name="message_list"),
    path("pesan/<int:pk>/", views.message_detail, name="message_detail"),
    path("pesan/<int:pk>/hapus/", views.message_delete, name="message_delete"),

    path("pengaturan/", views.site_settings, name="site_settings"),

    path("pengguna/", views.user_list, name="user_list"),
    path("pengguna/tambah/", views.user_form, name="user_create"),
    path("pengguna/<int:pk>/", views.user_form, name="user_edit"),
    path("pengguna/<int:pk>/sandi/", views.user_password, name="user_password"),
    path("pengguna/<int:pk>/hapus/", views.user_delete, name="user_delete"),
]
