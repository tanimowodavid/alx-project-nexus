from rest_framework import serializers
from .models import Cart, CartItem
from products.models import ProductVariant

class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()
    variant_name = serializers.ReadOnlyField(source='product_variant.variant_name')
    price = serializers.ReadOnlyField(source='product_variant.price')

    class Meta:
        model = CartItem
        fields = ['id', 'product_variant', 'variant_name', 'price', 'quantity', 'subtotal']

    def validate(self, data):
        variant = data.get('product_variant')
        quantity = data.get('quantity')

        # 1. Check if variant is active
        if not variant.is_active or not variant.product.is_active:
            raise serializers.ValidationError("This vehicle configuration is no longer available.")

        # 2. Check stock
        if variant.stock_quantity < quantity:
            raise serializers.ValidationError(f"Only {variant.stock_quantity} units available in stock.")

        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']
