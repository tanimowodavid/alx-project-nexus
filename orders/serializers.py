from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_snapshot', 'variant_snapshot', 
            'price_at_purchase', 'quantity'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'total_price', 'shipping_address_snapshot', 
            'items', 'created_at'
        ]
        read_only_fields = ['status', 'total_price', 'shipping_address_snapshot']
