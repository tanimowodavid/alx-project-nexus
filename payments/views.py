from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from orders.models import Order
from carts.models import Cart
from .models import Payment
from .services import PaymentService
import logging

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    """
    API endpoint to initiate a payment for an order.
    POST: Initialize a payment transaction
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Initiate payment for an order.
        
        Request body:
        {
            "order_id": integer,
            "payment_method": "card" or "transfer"
        }
        """
        try:
            order_id = request.data.get('order_id')
            payment_method = request.data.get('payment_method', 'card')
            
            if not order_id:
                return Response(
                    {"error": "order_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate order exists and belongs to user
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Check if order is pending
            if order.status != 'pending':
                return Response(
                    {"error": f"Cannot initiate payment for order with status '{order.status}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize payment
            payment_service = PaymentService()
            result = payment_service.process_payment(
                order_id=order_id,
                amount=order.total_price,
                email=request.user.email,
                payment_method=payment_method,
                currency="NGN"
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    """
    API endpoint to verify a payment transaction.
    Clears cart and updates order/stock only on successful verification.
    GET: Verify payment status using reference code
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Verify payment status. Clears cart on success.
        
        Query parameters:
        ?reference=<paystack_reference>
        """
        try:
            reference = request.query_params.get('reference')
            
            if not reference:
                return Response(
                    {"error": "reference parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            payment_service = PaymentService()
            result = payment_service.verify_payment(reference)
            
            if result['success']:
                # Clear cart only on successful payment verification
                with transaction.atomic():
                    try:
                        cart = Cart.objects.get(user=request.user)
                        cart.items.all().delete()
                        logger.info(f"Cart cleared for user {request.user.id} after successful payment")
                    except Cart.DoesNotExist:
                        pass  # Cart might not exist
                
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentDetailView(APIView):
    """
    API endpoint to retrieve payment details.
    GET: Get payment status and details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        """
        Get payment details by payment ID.
        """
        try:
            # Verify payment belongs to user's order
            payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
            
            payment_service = PaymentService()
            result = payment_service.get_payment_status(payment_id)
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error retrieving payment {payment_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefundPaymentView(APIView):
    """
    API endpoint to refund a payment.
    POST: Refund a successful payment
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        """
        Request a refund for a payment. Restores stock on successful refund.
        
        Request body (optional):
        {
            "amount": decimal (if not provided, full amount is refunded)
        }
        """
        try:
            # Verify payment belongs to user's order
            payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
            
            amount = request.data.get('amount')
            
            payment_service = PaymentService()
            result = payment_service.refund_payment(
                payment_id=payment_id,
                amount=float(amount) if amount else None
            )
            
            if result['success']:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError:
            return Response(
                {"error": "Invalid amount format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error processing refund for payment {payment_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderPaymentHistoryView(APIView):
    """
    API endpoint to retrieve payment history for an order.
    GET: Get all payment attempts for an order
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        """
        Get payment history for an order.
        """
        try:
            # Verify order belongs to user
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Get payment for this order (OneToOne relationship)
            try:
                payment = Payment.objects.get(order=order)
                payment_data = {
                    "id": payment.id,
                    "amount": str(payment.amount),
                    "status": payment.status,
                    "method": payment.method,
                    "tx_ref": payment.tx_ref,
                    "created_at": payment.created_at.isoformat()
                }
            except Payment.DoesNotExist:
                payment_data = None
            
            return Response(
                {
                    "success": True,
                    "order_id": order_id,
                    "order_status": order.status,
                    "payment": payment_data
                },
                status=status.HTTP_200_OK
            )
                
        except Exception as e:
            logger.error(f"Error retrieving payment history for order {order_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
