from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CheckoutView, paystack_callback, paystack_webhook, VerifyPaymentView

router = DefaultRouter()
router.register(r'my-orders', OrderViewSet, basename='orders')
router.register(r'checkout', CheckoutView, basename='checkout')

urlpatterns = [
    path('', include(router.urls)),
    path("verify-payment/<str:tx_ref>", VerifyPaymentView.as_view(), name="verify-payment"),
]
