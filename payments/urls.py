from django.urls import path
from .views import (
    InitiatePaymentView,
    VerifyPaymentView,
    PaymentDetailView,
    RefundPaymentView,
    OrderPaymentHistoryView
)

urlpatterns = [
    # Initialize payment for an order
    path('initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    
    # Verify payment using reference code
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    
    # Get payment details
    path('<int:payment_id>/', PaymentDetailView.as_view(), name='payment-detail'),
    
    # Refund a payment
    path('<int:payment_id>/refund/', RefundPaymentView.as_view(), name='refund-payment'),
    
    # Get payment history for an order
    path('order/<int:order_id>/history/', OrderPaymentHistoryView.as_view(), name='order-payment-history'),
]
