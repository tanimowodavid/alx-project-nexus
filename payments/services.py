import requests
from django.conf import settings
from django.db import transaction
from .models import Payment
from orders.models import Order, OrderItem
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Service class for handling payment operations"""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    
    def process_payment(self, order_id, amount, email, payment_method, currency="NGN"):
        """
        Initiate a payment transaction with Paystack.
        
        Args:
            order_id: The Order ID to associate with this payment
            amount: Amount to charge (in main currency unit)
            email: Customer email address
            payment_method: Payment method (e.g., "card", "transfer")
            currency: Currency code (default: NGN)
            
        Returns:
            dict with transaction details or error message
        """
        try:
            order = Order.objects.get(id=order_id)
            
            # Only allow payment initiation for pending orders
            if order.status != 'pending':
                return {
                    "success": False,
                    "error": f"Cannot initiate payment for order with status '{order.status}'"
                }
            
            # Check if payment amount matches order total
            if float(amount) != float(order.total_price):
                return {
                    "success": False,
                    "error": f"Payment amount {amount} does not match order total {order.total_price}"
                }
            
            # Create payment record with pending status
            with transaction.atomic():
                payment = Payment.objects.create(
                    order=order,
                    method=payment_method,
                    amount=amount,
                    status='pending',
                    tx_ref='TEMP'  # Will be updated with actual transaction ID
                )
                
                # Prepare Paystack request
                data = {
                    "email": email,
                    "amount": int(amount * 100),  # Paystack uses kobo/cents
                    "currency": currency,
                    "metadata": {
                        "order_id": order_id,
                        "payment_id": payment.id,
                        "customer_email": email
                    }
                }
                
                response = requests.post(
                    f"{self.BASE_URL}/transaction/initialize",
                    json=data,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status'):
                        # Update payment with actual transaction ID
                        payment.tx_ref = str(result['data']['reference'])
                        payment.save()
                        
                        logger.info(f"Payment initiated for order {order_id} with reference {payment.tx_ref}")
                        
                        return {
                            "success": True,
                            "payment_id": payment.id,
                            "authorization_url": result['data']['authorization_url'],
                            "access_code": result['data']['access_code'],
                            "reference": result['data']['reference'],
                            "message": "Payment initialized successfully"
                        }
                
                # If Paystack response failed, mark payment as failed
                payment.status = 'failed'
                payment.save()
                
                logger.error(f"Paystack initialization failed for order {order_id}: {response.text}")
                
                return {
                    "success": False,
                    "error": "Failed to initialize payment with provider",
                    "details": response.text
                }
                
        except Order.DoesNotExist:
            return {"success": False, "error": "Order not found"}
        except requests.RequestException as e:
            logger.error(f"Network error during payment initialization: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing payment for order {order_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error processing payment: {str(e)}"}
    
    def verify_payment(self, reference):
        """
        Verify payment status with Paystack using transaction reference.
        Updates order status and deducts stock only on successful verification.
        
        Args:
            reference: Paystack transaction reference
            
        Returns:
            dict with payment status and details
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/transaction/verify/{reference}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status'):
                    transaction_data = result['data']
                    
                    # Find payment record and update
                    try:
                        payment = Payment.objects.select_for_update().get(tx_ref=reference)
                        
                        if transaction_data['status'] == 'success':
                            with transaction.atomic():
                                # Update payment status
                                payment.status = 'success'
                                payment.save()
                                
                                # Update order status to confirmed
                                order = payment.order
                                order.status = 'confirmed'
                                order.save()
                                
                                # Deduct stock for all order items
                                for order_item in order.items.all():
                                    variant = order_item.product_variant
                                    variant.stock_quantity -= order_item.quantity
                                    variant.save()
                                    logger.info(f"Stock reduced for variant {variant.id}: -{order_item.quantity}")
                                
                                logger.info(f"Payment verified and confirmed for order {order.id}")
                                
                                return {
                                    "success": True,
                                    "payment_status": "success",
                                    "order_id": order.id,
                                    "order_status": "confirmed",
                                    "amount": transaction_data['amount'] / 100,
                                    "customer": transaction_data['customer']['email'],
                                    "message": "Payment verified successfully. Order confirmed and stock reduced."
                                }
                        else:
                            # Payment failed - mark payment and order as failed
                            payment.status = 'failed'
                            payment.save()
                            
                            order = payment.order
                            order.status = 'cancelled'
                            order.save()
                            
                            logger.warning(f"Payment failed for order {order.id}: {transaction_data['status']}")
                            
                            return {
                                "success": False,
                                "payment_status": transaction_data['status'],
                                "order_id": order.id,
                                "order_status": "cancelled",
                                "message": "Payment was not successful. Order has been cancelled."
                            }
                    except Payment.DoesNotExist:
                        logger.error(f"Payment record not found for reference {reference}")
                        return {
                            "success": False,
                            "error": "Payment record not found",
                            "reference": reference
                        }
                
                return {"success": False, "error": "Invalid payment response"}
                
        except requests.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error verifying payment {reference}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error verifying payment: {str(e)}"}
    
    def refund_payment(self, payment_id, amount=None):
        """
        Refund a payment. Refunds the full amount if amount is not specified.
        Restores stock when refund is successful.
        
        Args:
            payment_id: Payment ID to refund
            amount: Optional amount to refund (if not provided, full amount is refunded)
            
        Returns:
            dict with refund status
        """
        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)
            
            if payment.status != 'success':
                return {"success": False, "error": "Only successful payments can be refunded"}
            
            refund_amount = amount or payment.amount
            
            if refund_amount > payment.amount:
                return {"success": False, "error": "Refund amount exceeds payment amount"}
            
            # Prepare refund request
            data = {
                "transaction": payment.tx_ref,
                "amount": int(refund_amount * 100)  # Paystack uses kobo/cents
            }
            
            response = requests.post(
                f"{self.BASE_URL}/refund",
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status'):
                    with transaction.atomic():
                        payment.status = 'refunded'
                        payment.save()
                        
                        # Update order status and restore stock
                        order = payment.order
                        order.status = 'cancelled'
                        order.save()
                        
                        # Restore stock for all order items
                        for order_item in order.items.all():
                            variant = order_item.product_variant
                            variant.stock_quantity += order_item.quantity
                            variant.save()
                            logger.info(f"Stock restored for variant {variant.id}: +{order_item.quantity}")
                        
                        logger.info(f"Payment {payment_id} refunded. Stock restored for order {order.id}")
                        
                        return {
                            "success": True,
                            "refund_reference": result['data']['reference'],
                            "amount_refunded": refund_amount,
                            "message": "Refund processed successfully. Stock has been restored."
                        }
            
            logger.error(f"Refund failed for payment {payment_id}: {response.text}")
            
            return {
                "success": False,
                "error": "Failed to process refund",
                "details": response.text
            }
            
        except Payment.DoesNotExist:
            return {"success": False, "error": "Payment not found"}
        except requests.RequestException as e:
            logger.error(f"Network error during refund: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing refund for payment {payment_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error processing refund: {str(e)}"}
    
    def get_payment_status(self, payment_id):
        """
        Get the current status of a payment.
        
        Args:
            payment_id: Payment ID to check
            
        Returns:
            dict with payment status details
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            return {
                "success": True,
                "payment_id": payment.id,
                "order_id": payment.order.id,
                "order_status": payment.order.status,
                "amount": str(payment.amount),
                "status": payment.status,
                "method": payment.method,
                "tx_ref": payment.tx_ref,
                "created_at": payment.created_at.isoformat()
            }
            
        except Payment.DoesNotExist:
            return {"success": False, "error": "Payment not found"}
        except Exception as e:
            logger.error(f"Error retrieving payment {payment_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error retrieving payment: {str(e)}"}


