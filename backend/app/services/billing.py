import os
import requests
from typing import Dict, Optional


class LemonSqueezyBilling:
    def __init__(self):
        self.api_key = os.getenv("LEMON_SQUEEZY_API_KEY")
        self.store_id = os.getenv("LEMON_SQUEEZY_STORE_ID")
        self.base_url = "https://api.lemonsqueezy.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def create_checkout(
        self,
        variant_id: str,
        customer_email: str,
        custom_data: Optional[Dict] = None
    ) -> Dict:
        url = f"{self.base_url}/checkouts"
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": customer_email,
                        "custom": custom_data or {}
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": self.store_id
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": variant_id
                        }
                    }
                }
            }
        }

        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    async def create_subscription(
        self,
        customer_id: str,
        variant_id: str
    ) -> Dict:
        url = f"{self.base_url}/subscriptions"
        payload = {
            "data": {
                "type": "subscriptions",
                "relationships": {
                    "customer": {
                        "data": {
                            "type": "customers",
                            "id": customer_id
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": variant_id
                        }
                    }
                }
            }
        }

        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    async def get_subscription(self, subscription_id: str) -> Dict:
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    async def cancel_subscription(self, subscription_id: str) -> Dict:
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()

    async def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        import hmac
        import hashlib

        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)


class SubscriptionPlans:
    FREE = {
        "name": "Free",
        "price": 0,
        "credits": 100,
        "features": [
            "100 AI responses per month",
            "Basic support",
            "Single content upload"
        ]
    }

    STARTER = {
        "name": "Starter",
        "price": 29,
        "credits": 1000,
        "variant_id": "starter_variant_id",
        "features": [
            "1,000 AI responses per month",
            "Unlimited content uploads",
            "Email support",
            "Custom widget styling"
        ]
    }

    PRO = {
        "name": "Pro",
        "price": 49,
        "credits": -1,
        "variant_id": "pro_variant_id",
        "features": [
            "Unlimited AI responses",
            "Unlimited content uploads",
            "Priority support",
            "Custom widget styling",
            "Advanced analytics",
            "API access"
        ]
    }
