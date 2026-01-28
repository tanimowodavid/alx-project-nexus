from django.db import models
from django.conf import settings


# Create your models here.
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50)  # e.g., home, office
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} - {self.street}, {self.city}, {self.state}, {self.country}"

    def save(self, *args, **kwargs):
        # 1. Check if this is the user's only address
        user_addresses = Address.objects.filter(user=self.user)
        
        if not user_addresses.exists():
            self.is_default = True
            
        # 2. If this is being set as default, unset others
        if self.is_default:
            user_addresses.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        # 3. Prevent unsetting the default if it's the only one
        elif not user_addresses.filter(is_default=True).exclude(pk=self.pk).exists():
            self.is_default = True

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'

