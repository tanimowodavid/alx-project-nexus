from rest_framework import serializers
from .models import Cart, CartItem


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

        # Check if variant is active (not deleted)
        if not variant.is_active or not variant.product.is_active:
            raise serializers.ValidationError("This product is no longer available.")

        # Check if store has enough stock
        if variant.stock_quantity < quantity:
            raise serializers.ValidationError(f"Only {variant.stock_quantity} units available in stock.")

        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']
