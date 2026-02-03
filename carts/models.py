from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import ProductVariant
from django.db.models import F, Sum


# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def total_price(self):
        result = self.items.aggregate(
            total=Sum(F('quantity') * F('product_variant__price'))
        )
        return result['total'] or 0


"""
Model for items contained in the cart
"""
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product_variant} in Cart {self.cart.id}"

    @property
    def subtotal(self):
        return self.product_variant.price * self.quantity

    class Meta:
        unique_together = ('cart', 'product_variant') # Prevents duplicate rows for the same variant

