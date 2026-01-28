from rest_framework import serializers
from .models import Product, ProductVariant, Category
import uuid
from django.utils.text import slugify


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "description", "parent"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['sku', 'variant_name', 'price', 'stock_quantity']


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True)
    category = serializers.SlugRelatedField(
        many=True,
        slug_field="slug",
        queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'variants']

    def create(self, validated_data):
        variants_data = validated_data.pop('variants')
        categories = validated_data.pop("category")

        product = Product.objects.create(**validated_data)

        # assign categories properly
        product.category.set(categories)

        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
        return product


class ProductVariantListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")

    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "product_name",
            "variant_name",
            "price",
            "stock_quantity",
        ]

class ProductVariantDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_description = serializers.CharField(source="product.description")

    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "product_name",
            "product_description",
            "variant_name",
            "price",
            "stock_quantity",
        ]
