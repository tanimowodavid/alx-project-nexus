from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from carts.models import Cart
from address.models import Address
from .models import Order, OrderItem
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class CheckoutView(APIView):
    """Create an order from cart items. Payment must be completed to confirm the order."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        try:
            cart = Cart.objects.get(user=user)
            
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # Get default address
            address = Address.objects.filter(user=user, is_default=True).first()
            if not address:
                return Response({"error": "No default address found"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate stock availability before creating order
            for item in cart.items.all():
                variant = item.product_variant
                if variant.stock_quantity < item.quantity:
                    return Response(
                        {"error": f"Not enough stock for {variant.variant_name}. Available: {variant.stock_quantity}, Requested: {item.quantity}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            with transaction.atomic():
                # 1. Create the Order with 'pending' status
                order = Order.objects.create(
                    user=user,
                    shipping_address_snapshot=str(address),
                    total_price=cart.total_price,
                    status='pending'
                )

                # 2. Create OrderItems (DO NOT reduce stock yet - wait for payment verification)
                for item in cart.items.all():
                    variant = item.product_variant
                    
                    OrderItem.objects.create(
                        order=order,
                        product_variant=variant,
                        price_at_purchase=variant.price,
                        quantity=item.quantity
                    )

                # Return order details for payment initiation
                return Response(
                    {
                        "message": "Order created. Please complete payment to confirm.",
                        "order_id": order.id,
                        "total_price": str(order.total_price),
                        "status": order.status
                    },
                    status=status.HTTP_201_CREATED
                )

        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Checkout error for user {user.id}: {str(e)}", exc_info=True)
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


