from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from products.models import ProductVariant
from .serializers import CartSerializer

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Using select_related/prefetch_related improves performance
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product_variant')

    def create(self, request, *args, **kwargs):
        variant_slug = request.data.get('variant_slug')
        quantity = int(request.data.get('quantity', 1))
        variant = get_object_or_404(ProductVariant, slug=variant_slug)
        
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        # Use 'product_variant' to match your serializer/model
        item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant)
        
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        
        item.save()
        return Response({"message": "Item added to cart"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def reduce_item(self, request):
        variant_slug = request.data.get('variant_slug')
        quantity = int(request.data.get('quantity', 1))
        cart = self.get_queryset().first()
        
        item = get_object_or_404(CartItem, cart=cart, product_variant__slug=variant_slug)
        
        if item.quantity <= quantity:
            item.delete()
            return Response({"message": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)
        
        item.quantity -= quantity
        item.save()
        return Response({"message": f"Quantity reduced by {quantity}"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        variant_slug = request.data.get('variant_slug')
        cart = self.get_queryset().first()
        
        item = get_object_or_404(CartItem, cart=cart, product_variant__slug=variant_slug)
        item.delete()
        return Response({"message": "Item completely removed"}, status=status.HTTP_204_NO_CONTENT)
