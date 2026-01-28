from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import AddressViewSet

router = SimpleRouter()
router.register(r'', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]
