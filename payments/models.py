from django.db import models

# Create your models here.
class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=50) # e.g., "Card", "Transfer"
    tx_ref = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"
