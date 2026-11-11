import hmac
import hashlib
import base64
import requests
from decimal import Decimal
from django.conf import settings


class NepalPaymentGateway:
    """
    Unified payment gateway adapter for Nepal local payment providers:
    eSewa (ePay v2), Khalti (epayment v2), and Fonepay.
    """

    @staticmethod
    def generate_esewa_signature(total_amount: Decimal, transaction_uuid: str, product_code: str, secret_key: str) -> str:
        """Generates HMAC-SHA256 signature required by eSewa ePay v2."""
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        secret_bytes = secret_key.encode("utf-8")
        message_bytes = message.encode("utf-8")
        signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256).digest()
        return base64.b64encode(signature).decode("utf-8")

    @classmethod
    def initiate_khalti_payment(cls, return_url: str, website_url: str, amount_paisa: int, purchase_order_id: str, purchase_order_name: str):
        """
        Initiates a Khalti ePayment v2 transaction and returns the payment_url.
        Amount is in Paisa (1 NPR = 100 Paisa).
        """
        secret_key = getattr(settings, "KHALTI_SECRET_KEY", "test_secret_key")
        base_url = getattr(settings, "KHALTI_BASE_URL", "https://a.khalti.com/api/v2")

        headers = {
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount_paisa,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": purchase_order_name,
        }
        try:
            res = requests.post(f"{base_url}/epayment/initiate/", json=payload, headers=headers, timeout=10)
            return res.json()
        except requests.RequestException as e:
            return {"error": str(e), "success": False}

    @classmethod
    def verify_khalti_lookup(cls, pidx: str):
        """Verifies status of transaction via Khalti lookup endpoint."""
        secret_key = getattr(settings, "KHALTI_SECRET_KEY", "test_secret_key")
        base_url = getattr(settings, "KHALTI_BASE_URL", "https://a.khalti.com/api/v2")

        headers = {
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json",
        }
        try:
            res = requests.post(f"{base_url}/epayment/lookup/", json={"pidx": pidx}, headers=headers, timeout=10)
            return res.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "Failed"}
