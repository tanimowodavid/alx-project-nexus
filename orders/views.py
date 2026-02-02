from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from carts.models import Cart
from address.models import Address
from .models import Order, OrderItem
from .serializers import OrderSerializer
from .services import PaystackService
from django.shortcuts import get_object_or_404
from .tasks import process_order_payment


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view allows users to view their order history.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class CheckoutView(viewsets.ViewSet):
    """
    This view handles the 'Checkout' button logic.
    """
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        # Check if cart exist and not empty
        if not cart or not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Confirm address
        address = Address.objects.filter(user=user, is_default=True).first()
        if not address:
            return Response({"error": "Please set a default shipping address"}, status=status.HTTP_400_BAD_REQUEST)

        # Pre-check Stock
        for item in cart.items.all():
            if item.product_variant.stock_quantity < item.quantity:
                return Response(
                    {"error": f"Item {item.product_variant.variant_name} is out of stock"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create Pending Order & Snapshots
        order = Order.objects.create(
            user=user,
            shipping_address_snapshot=str(address),
            total_price=cart.total_price,
            status='pending'
        )

        # Create the order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product_snapshot=item.product_variant.product.name,
                variant_snapshot=item.product_variant.variant_name,
                price_at_purchase=item.product_variant.price,
                quantity=item.quantity
            )

        # Generate Paystack Link
        paystack = PaystackService()
        paystack_data = paystack.initialize_paystack_payment(
            email=user.email,
            amount=order.total_price,
            tx_ref=order.tx_ref
        )

        if paystack_data.get('status'):
            checkout_url = paystack_data['data']['authorization_url']

            return Response({
                "message": "Payment link generated",
                "tx_ref": str(order.tx_ref),
                "checkout_url": checkout_url
            }, status=status.HTTP_201_CREATED)


        return Response(
            {"error": "Could not generate payment link"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VerifyPaymentView(APIView):
    def get(self, request: Request, tx_ref):
        order = get_object_or_404(Order, tx_ref=tx_ref)

        paystack = PaystackService()
        verification = paystack.verify_payment(order.tx_ref)

        if verification.get("status") and verification['data']['status'] == 'success':
            process_order_payment.delay(order.id)
            return Response({"message": "Payment verified, processing order."}, status=200)

        return Response({"status": "Payment Failed"}, status.HTTP_400_BAD_REQUEST)
    

