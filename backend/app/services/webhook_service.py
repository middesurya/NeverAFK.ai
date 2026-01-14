"""
Webhook Service for managing webhook subscriptions and event delivery.

Provides:
- Webhook registration and management
- Event dispatching to subscribed webhooks
- HMAC payload signing for security
- Retry mechanism for failed deliveries
- Delivery status tracking

PRD-024: Webhook System Implementation
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import hmac
import hashlib
import uuid
import re
import asyncio
import json
import logging

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Status of a webhook delivery attempt."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class WebhookEvent(Enum):
    """Supported webhook event types."""
    CHAT_COMPLETED = "chat.completed"
    ESCALATION_CREATED = "escalation.created"
    FEEDBACK_RECEIVED = "feedback.received"
    CONVERSATION_STARTED = "conversation.started"
    WILDCARD = "*"


# List of valid event type strings
VALID_EVENT_TYPES = {
    "chat.completed",
    "escalation.created",
    "feedback.received",
    "conversation.started",
    "*",  # Wildcard for all events
}


@dataclass
class Webhook:
    """
    Represents a registered webhook subscription.

    Attributes:
        id: Unique identifier for the webhook
        url: The URL to send webhook events to
        events: List of event types this webhook is subscribed to
        secret: Secret key for signing payloads (HMAC)
        active: Whether the webhook is currently active
        created_at: When the webhook was created
        name: Optional human-readable name
        description: Optional description of the webhook's purpose
    """
    id: str
    url: str
    events: List[str]
    secret: str
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    name: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert webhook to dictionary for serialization."""
        return {
            "id": self.id,
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "name": self.name,
            "description": self.description,
        }


@dataclass
class WebhookDelivery:
    """
    Represents a webhook delivery attempt.

    Attributes:
        id: Unique identifier for the delivery
        webhook_id: ID of the webhook this delivery is for
        event: The event type being delivered
        payload: The payload data being sent
        status: Current delivery status
        attempts: Number of delivery attempts made
        response_code: HTTP response code from the target
        response_body: Response body from the target
        created_at: When the delivery was created
        delivered_at: When the delivery was successfully completed
        next_retry_at: When the next retry should be attempted
    """
    id: str
    webhook_id: str
    event: str
    payload: Dict[str, Any]
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert delivery to dictionary for serialization."""
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event": self.event,
            "payload": self.payload,
            "status": self.status.value,
            "attempts": self.attempts,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
        }


class WebhookService:
    """
    Service for managing webhooks and event delivery.

    Handles webhook registration, event dispatching, payload signing,
    retry logic, and delivery tracking.
    """

    # URL validation regex
    URL_REGEX = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    def __init__(self, max_retry_attempts: int = 5, base_retry_delay: float = 1.0):
        """
        Initialize the webhook service.

        Args:
            max_retry_attempts: Maximum number of retry attempts for failed deliveries
            base_retry_delay: Base delay in seconds for exponential backoff
        """
        self._webhooks: Dict[str, Webhook] = {}
        self._deliveries: List[WebhookDelivery] = []
        self.max_retry_attempts = max_retry_attempts
        self.base_retry_delay = base_retry_delay

    def register(
        self,
        url: str,
        events: List[str],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Webhook:
        """
        Register a new webhook.

        Args:
            url: The URL to send webhook events to
            events: List of event types to subscribe to
            name: Optional human-readable name
            description: Optional description

        Returns:
            The created Webhook object

        Raises:
            ValueError: If URL is invalid or events list is empty/contains invalid types
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValueError(f"Invalid webhook URL: {url}")

        # Validate events
        if not events:
            raise ValueError("At least one event type is required")

        for event in events:
            if event not in VALID_EVENT_TYPES:
                raise ValueError(f"Invalid event type: {event}")

        # Create webhook
        webhook = Webhook(
            id=f"wh_{uuid.uuid4().hex[:16]}",
            url=url,
            events=events,
            secret=self._generate_secret(),
            name=name,
            description=description
        )

        self._webhooks[webhook.id] = webhook
        logger.info(f"Registered webhook {webhook.id} for events: {events}")

        return webhook

    def get(self, webhook_id: str) -> Optional[Webhook]:
        """
        Get a webhook by ID.

        Args:
            webhook_id: The ID of the webhook to retrieve

        Returns:
            The Webhook object or None if not found
        """
        return self._webhooks.get(webhook_id)

    def list(self) -> List[Webhook]:
        """
        List all registered webhooks.

        Returns:
            List of all Webhook objects
        """
        return list(self._webhooks.values())

    def update(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        active: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Webhook:
        """
        Update a webhook's configuration.

        Args:
            webhook_id: The ID of the webhook to update
            url: New URL (optional)
            events: New events list (optional)
            active: New active status (optional)
            name: New name (optional)
            description: New description (optional)

        Returns:
            The updated Webhook object

        Raises:
            ValueError: If webhook not found or invalid values provided
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")

        if url is not None:
            if not self._validate_url(url):
                raise ValueError(f"Invalid webhook URL: {url}")
            webhook.url = url

        if events is not None:
            if not events:
                raise ValueError("At least one event type is required")
            for event in events:
                if event not in VALID_EVENT_TYPES:
                    raise ValueError(f"Invalid event type: {event}")
            webhook.events = events

        if active is not None:
            webhook.active = active

        if name is not None:
            webhook.name = name

        if description is not None:
            webhook.description = description

        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    def delete(self, webhook_id: str) -> None:
        """
        Delete a webhook.

        Args:
            webhook_id: The ID of the webhook to delete

        Raises:
            ValueError: If webhook not found
        """
        if webhook_id not in self._webhooks:
            raise ValueError(f"Webhook not found: {webhook_id}")

        del self._webhooks[webhook_id]
        logger.info(f"Deleted webhook {webhook_id}")

    def deactivate(self, webhook_id: str) -> None:
        """
        Deactivate a webhook.

        Args:
            webhook_id: The ID of the webhook to deactivate

        Raises:
            ValueError: If webhook not found
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")

        webhook.active = False
        logger.info(f"Deactivated webhook {webhook_id}")

    def activate(self, webhook_id: str) -> None:
        """
        Activate a webhook.

        Args:
            webhook_id: The ID of the webhook to activate

        Raises:
            ValueError: If webhook not found
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook not found: {webhook_id}")

        webhook.active = True
        logger.info(f"Activated webhook {webhook_id}")

    def get_supported_events(self) -> List[str]:
        """
        Get list of all supported event types.

        Returns:
            List of supported event type strings
        """
        return list(VALID_EVENT_TYPES)

    def sign_payload(self, payload: str, secret: str) -> str:
        """
        Sign a payload using HMAC-SHA256.

        Args:
            payload: The payload string to sign
            secret: The secret key to use for signing

        Returns:
            The hexadecimal signature string
        """
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify a payload signature.

        Args:
            payload: The payload string to verify
            signature: The signature to check
            secret: The secret key used for signing

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected_signature)

    async def dispatch(self, event: str, payload: Dict[str, Any]) -> List[WebhookDelivery]:
        """
        Dispatch an event to all subscribed webhooks.

        Args:
            event: The event type being dispatched
            payload: The payload data to send

        Returns:
            List of WebhookDelivery objects created
        """
        deliveries = []

        for webhook in self._webhooks.values():
            if not webhook.active:
                continue

            # Check if webhook is subscribed to this event
            if "*" not in webhook.events and event not in webhook.events:
                continue

            # Create delivery
            delivery = self._create_delivery(webhook.id, event, payload)
            self._deliveries.append(delivery)

            # Attempt delivery
            await self._attempt_delivery(delivery, webhook)
            deliveries.append(delivery)

        return deliveries

    async def retry_failed_deliveries(self) -> int:
        """
        Retry all failed deliveries that haven't exceeded max attempts.

        Returns:
            Number of deliveries retried
        """
        retried = 0

        for delivery in self._deliveries:
            if delivery.status != DeliveryStatus.FAILED:
                continue

            if delivery.attempts >= self.max_retry_attempts:
                continue

            webhook = self._webhooks.get(delivery.webhook_id)
            if not webhook or not webhook.active:
                continue

            await self._attempt_delivery(delivery, webhook)
            retried += 1

        return retried

    def calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay using exponential backoff.

        Args:
            attempt: The attempt number (1-based)

        Returns:
            Delay in seconds before next retry
        """
        return self.base_retry_delay * (2 ** (attempt - 1))

    def get_deliveries(self, webhook_id: str) -> List[WebhookDelivery]:
        """
        Get all deliveries for a webhook.

        Args:
            webhook_id: The webhook ID to filter by

        Returns:
            List of WebhookDelivery objects for the webhook
        """
        return [d for d in self._deliveries if d.webhook_id == webhook_id]

    def get_deliveries_by_status(self, status: DeliveryStatus) -> List[WebhookDelivery]:
        """
        Get deliveries filtered by status.

        Args:
            status: The status to filter by

        Returns:
            List of WebhookDelivery objects with the given status
        """
        return [d for d in self._deliveries if d.status == status]

    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """
        Get a specific delivery by ID.

        Args:
            delivery_id: The delivery ID to retrieve

        Returns:
            The WebhookDelivery object or None if not found
        """
        for delivery in self._deliveries:
            if delivery.id == delivery_id:
                return delivery
        return None

    def _validate_url(self, url: str) -> bool:
        """
        Validate a webhook URL.

        Args:
            url: The URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        return bool(self.URL_REGEX.match(url))

    def _generate_secret(self) -> str:
        """
        Generate a secure random secret for webhook signing.

        Returns:
            A 32-character hexadecimal secret string
        """
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    def _create_delivery(
        self,
        webhook_id: str,
        event: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """
        Create a new delivery record.

        Args:
            webhook_id: The webhook ID
            event: The event type
            payload: The payload data

        Returns:
            A new WebhookDelivery object
        """
        return WebhookDelivery(
            id=f"del_{uuid.uuid4().hex[:16]}",
            webhook_id=webhook_id,
            event=event,
            payload=payload
        )

    async def _attempt_delivery(
        self,
        delivery: WebhookDelivery,
        webhook: Webhook
    ) -> None:
        """
        Attempt to deliver a webhook event.

        Args:
            delivery: The delivery to attempt
            webhook: The webhook to deliver to
        """
        delivery.attempts += 1

        try:
            # Prepare payload
            payload_json = json.dumps({
                "event": delivery.event,
                "payload": delivery.payload,
                "delivery_id": delivery.id,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Sign payload
            signature = self.sign_payload(payload_json, webhook.secret)

            # Send request
            response_code, response_body = await self._send_webhook(
                url=webhook.url,
                payload=payload_json,
                signature=signature
            )

            # Update delivery
            delivery.response_code = response_code
            delivery.response_body = response_body

            if 200 <= response_code < 300:
                delivery.status = DeliveryStatus.SUCCESS
                delivery.delivered_at = datetime.utcnow()
                logger.info(f"Delivery {delivery.id} succeeded with status {response_code}")
            else:
                delivery.status = DeliveryStatus.FAILED
                logger.warning(f"Delivery {delivery.id} failed with status {response_code}")

        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.response_body = str(e)
            logger.error(f"Delivery {delivery.id} failed with exception: {e}")

    async def _send_webhook(
        self,
        url: str,
        payload: str,
        signature: str
    ) -> tuple[int, str]:
        """
        Send the webhook HTTP request.

        Args:
            url: The target URL
            payload: The JSON payload string
            signature: The HMAC signature

        Returns:
            Tuple of (status_code, response_body)
        """
        if httpx is None:
            raise RuntimeError("httpx is required for webhook delivery")

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
            "User-Agent": "StrongMVP-Webhook/1.0"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=payload, headers=headers)
            return response.status_code, response.text


# Singleton instance
webhook_service = WebhookService()
