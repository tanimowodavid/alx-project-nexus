import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PaystackService:
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    def initialize_paystack_payment(self, email, amount, tx_ref):
        """
        Sends order details to Paystack and returns a payment URL.
        """
        url = self.base_url + "/transaction/initialize"
        # Paystack expects amount in KOBO so i will multiply amount by 100
        data = {
            "email": email,
            "amount": int(amount * 100),
            "reference": str(tx_ref),
            "callback_url": f"http://localhost:8000/api/orders/verify-payment/{tx_ref}",
        }
        
        try:
            res = requests.post(url, headers=self.headers, json=data)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Paystack Error: {e}')
            return None


    def verify_payment(self, tx_ref):
        """
        Sends order reference to Paystack and returns a payment status.
        """
        url = self.base_url + f"/transaction/verify/{tx_ref}"

        try:
            res = requests.get(url, headers=self.headers)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'Paystack verification Error: {e}')
            return None