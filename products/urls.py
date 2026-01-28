from django.urls import path
from .views import (
    ProductCreateView,
    ProductUpdateView,
    VariantDetailView,
    VariantListView,
    CategoryCreateView,
)

urlpatterns = [
    # Public
    path("", VariantListView.as_view(), name="product-list"),
    path("<str:sku>/", VariantDetailView.as_view(), name="product-detail"),

    # Admin
    path("admin/categories/create/", CategoryCreateView.as_view()),
    path("admin/products/create/", ProductCreateView.as_view(), name="product-create"),
    path("admin/products/<slug:slug>/update/", ProductUpdateView.as_view(), name="product-update"),
]
