from django.urls import path
from .views import (
    ProductCreateView,
    ProductUpdateView,
    ProductDetailView,
    ProductListView,
    CategoryCreateView,
)

urlpatterns = [
    # Public
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),

    # Admin
    path("admin/categories/create/", CategoryCreateView.as_view()),
    path("admin/products/create/", ProductCreateView.as_view(), name="product-create"),
    path("admin/products/<slug:slug>/update/", ProductUpdateView.as_view(), name="product-update"),
]
