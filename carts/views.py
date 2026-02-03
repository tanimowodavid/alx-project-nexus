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

    # --- CORE CRUD OPERATIONS ---
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product_variant')

    def create(self, request, *args, **kwargs):
        variant_sku = request.data.get('variant_sku')
        quantity = int(request.data.get('quantity', 1))
        variant = get_object_or_404(ProductVariant, sku=variant_sku)
        
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant)
        
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        
        item.save()
        return Response({"message": "Item added to cart"}, status=status.HTTP_201_CREATED)

    # --- QUANTITY MANAGEMENT ---
    @action(detail=False, methods=['post'])
    def reduce_item(self, request):
        variant_sku = request.data.get('variant_sku')
        quantity = int(request.data.get('quantity', 1))
        cart = self.get_queryset().first()
        
        item = get_object_or_404(CartItem, cart=cart, product_variant__sku=variant_sku)
        
        if item.quantity <= quantity:
            item.delete()
            return Response({"message": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)
        
        item.quantity -= quantity
        item.save()
        return Response({"message": f"Quantity reduced by {quantity}"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        variant_sku = request.data.get('variant_sku')
        cart = self.get_queryset().first()
        
        item = get_object_or_404(CartItem, cart=cart, product_variant__sku=variant_sku)
        item.delete()
        return Response({"message": "Item completely removed"}, status=status.HTTP_204_NO_CONTENT)
    
    def destroy(self, request, *args, **kwargs):
        """
        Overridden to prevent users from deleting their cart instance.
        """
        return Response(
            {"error": "Carts cannot be deleted. Use 'remove_item' or 'clear_cart' instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
