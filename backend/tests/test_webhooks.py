"""
Comprehensive tests for webhook functionality.
Tests cover:
- Webhook registration and management
- Event types (chat.completed, escalation.created, etc.)
- Payload signing (HMAC)
- Retry mechanism
- Delivery status tracking
- Webhook dispatching
- Error handling
- Edge cases
"""

import pytest
import time
import asyncio
import json
import hmac
import hashlib
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import webhook components
from app.services.webhook_service import (
    Webhook,
    WebhookDelivery,
    WebhookService,
    WebhookEvent,
    DeliveryStatus,
    webhook_service,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def service():
    """Create a fresh webhook service for each test."""
    return WebhookService()


@pytest.fixture
def sample_webhook(service):
    """Create a sample webhook for testing."""
    return service.register(
        url="https://example.com/webhook",
        events=["chat.completed", "escalation.created"]
    )


@pytest.fixture
def sample_payload():
    """Create a sample payload for testing."""
    return {
        "event": "chat.completed",
        "data": {
            "conversation_id": "conv_123",
            "user_id": "user_456",
            "message_count": 5,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing deliveries."""
    with patch('app.services.webhook_service.httpx') as mock:
        mock_client = AsyncMock()
        mock.AsyncClient.return_value.__aenter__.return_value = mock_client
        yield mock_client


# =============================================================================
# Test Webhook Dataclass
# =============================================================================

class TestWebhookDataclass:
    """Tests for Webhook dataclass."""

    def test_webhook_creation_with_required_fields(self):
        """Test creating a webhook with required fields."""
        webhook = Webhook(
            id="wh_123",
            url="https://example.com/webhook",
            events=["chat.completed"],
            secret="secret_abc"
        )
        assert webhook.id == "wh_123"
        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == ["chat.completed"]
        assert webhook.secret == "secret_abc"
        assert webhook.active is True

    def test_webhook_creation_with_all_fields(self):
        """Test creating a webhook with all fields."""
        created_at = datetime.utcnow()
        webhook = Webhook(
            id="wh_123",
            url="https://example.com/webhook",
            events=["chat.completed", "escalation.created"],
            secret="secret_abc",
            active=False,
            created_at=created_at,
            name="Test Webhook",
            description="A test webhook"
        )
        assert webhook.active is False
        assert webhook.created_at == created_at
        assert webhook.name == "Test Webhook"
        assert webhook.description == "A test webhook"

    def test_webhook_defaults(self):
        """Test webhook default values."""
        webhook = Webhook(
            id="wh_123",
            url="https://example.com/webhook",
            events=["chat.completed"],
            secret="secret_abc"
        )
        assert webhook.active is True
        assert webhook.created_at is not None
        assert webhook.name is None
        assert webhook.description is None


# =============================================================================
# Test WebhookDelivery Dataclass
# =============================================================================

class TestWebhookDeliveryDataclass:
    """Tests for WebhookDelivery dataclass."""

    def test_delivery_creation_with_required_fields(self):
        """Test creating a delivery with required fields."""
        delivery = WebhookDelivery(
            id="del_123",
            webhook_id="wh_456",
            event="chat.completed",
            payload={"data": "test"}
        )
        assert delivery.id == "del_123"
        assert delivery.webhook_id == "wh_456"
        assert delivery.event == "chat.completed"
        assert delivery.payload == {"data": "test"}

    def test_delivery_default_status(self):
        """Test delivery default status is pending."""
        delivery = WebhookDelivery(
            id="del_123",
            webhook_id="wh_456",
            event="chat.completed",
            payload={}
        )
        assert delivery.status == DeliveryStatus.PENDING

    def test_delivery_default_attempts(self):
        """Test delivery default attempts is 0."""
        delivery = WebhookDelivery(
            id="del_123",
            webhook_id="wh_456",
            event="chat.completed",
            payload={}
        )
        assert delivery.attempts == 0

    def test_delivery_with_response_info(self):
        """Test delivery with response information."""
        delivery = WebhookDelivery(
            id="del_123",
            webhook_id="wh_456",
            event="chat.completed",
            payload={},
            status=DeliveryStatus.SUCCESS,
            attempts=1,
            response_code=200,
            response_body="OK",
            delivered_at=datetime.utcnow()
        )
        assert delivery.status == DeliveryStatus.SUCCESS
        assert delivery.response_code == 200
        assert delivery.response_body == "OK"


# =============================================================================
# Test Webhook Registration
# =============================================================================

class TestWebhookRegistration:
    """Tests for webhook registration."""

    def test_register_webhook_basic(self, service):
        """Test basic webhook registration."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"]
        )
        assert webhook.id is not None
        assert webhook.url == "https://example.com/webhook"
        assert webhook.events == ["chat.completed"]
        assert webhook.secret is not None
        assert len(webhook.secret) > 0

    def test_register_webhook_multiple_events(self, service):
        """Test registering webhook with multiple events."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed", "escalation.created", "feedback.received"]
        )
        assert len(webhook.events) == 3
        assert "chat.completed" in webhook.events
        assert "escalation.created" in webhook.events
        assert "feedback.received" in webhook.events

    def test_register_webhook_with_name(self, service):
        """Test registering webhook with a name."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"],
            name="Production Webhook"
        )
        assert webhook.name == "Production Webhook"

    def test_register_webhook_with_description(self, service):
        """Test registering webhook with a description."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"],
            description="Webhook for production notifications"
        )
        assert webhook.description == "Webhook for production notifications"

    def test_register_webhook_generates_unique_ids(self, service):
        """Test that each webhook gets a unique ID."""
        webhook1 = service.register(url="https://example1.com/webhook", events=["chat.completed"])
        webhook2 = service.register(url="https://example2.com/webhook", events=["chat.completed"])
        assert webhook1.id != webhook2.id

    def test_register_webhook_generates_unique_secrets(self, service):
        """Test that each webhook gets a unique secret."""
        webhook1 = service.register(url="https://example1.com/webhook", events=["chat.completed"])
        webhook2 = service.register(url="https://example2.com/webhook", events=["chat.completed"])
        assert webhook1.secret != webhook2.secret

    def test_register_webhook_stored_in_service(self, service):
        """Test that registered webhook is stored in service."""
        webhook = service.register(url="https://example.com/webhook", events=["chat.completed"])
        assert webhook.id in service._webhooks
        assert service._webhooks[webhook.id] == webhook

    def test_register_webhook_invalid_url(self, service):
        """Test registering webhook with invalid URL raises error."""
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            service.register(url="not-a-url", events=["chat.completed"])

    def test_register_webhook_empty_events(self, service):
        """Test registering webhook with empty events raises error."""
        with pytest.raises(ValueError, match="At least one event type is required"):
            service.register(url="https://example.com/webhook", events=[])

    def test_register_webhook_invalid_event_type(self, service):
        """Test registering webhook with invalid event type raises error."""
        with pytest.raises(ValueError, match="Invalid event type"):
            service.register(url="https://example.com/webhook", events=["invalid.event"])


# =============================================================================
# Test Webhook Management
# =============================================================================

class TestWebhookManagement:
    """Tests for webhook management operations."""

    def test_get_webhook_by_id(self, service, sample_webhook):
        """Test getting a webhook by ID."""
        retrieved = service.get(sample_webhook.id)
        assert retrieved is not None
        assert retrieved.id == sample_webhook.id
        assert retrieved.url == sample_webhook.url

    def test_get_webhook_not_found(self, service):
        """Test getting a non-existent webhook returns None."""
        result = service.get("nonexistent_id")
        assert result is None

    def test_list_webhooks(self, service):
        """Test listing all webhooks."""
        service.register(url="https://example1.com/webhook", events=["chat.completed"])
        service.register(url="https://example2.com/webhook", events=["escalation.created"])

        webhooks = service.list()
        assert len(webhooks) == 2

    def test_list_webhooks_empty(self, service):
        """Test listing webhooks when none registered."""
        webhooks = service.list()
        assert webhooks == []

    def test_update_webhook_url(self, service, sample_webhook):
        """Test updating webhook URL."""
        updated = service.update(sample_webhook.id, url="https://newurl.com/webhook")
        assert updated.url == "https://newurl.com/webhook"

    def test_update_webhook_events(self, service, sample_webhook):
        """Test updating webhook events."""
        updated = service.update(sample_webhook.id, events=["feedback.received"])
        assert updated.events == ["feedback.received"]

    def test_update_webhook_active_status(self, service, sample_webhook):
        """Test updating webhook active status."""
        updated = service.update(sample_webhook.id, active=False)
        assert updated.active is False

    def test_update_webhook_not_found(self, service):
        """Test updating non-existent webhook raises error."""
        with pytest.raises(ValueError, match="Webhook not found"):
            service.update("nonexistent_id", url="https://example.com/webhook")

    def test_delete_webhook(self, service, sample_webhook):
        """Test deleting a webhook."""
        service.delete(sample_webhook.id)
        assert service.get(sample_webhook.id) is None

    def test_delete_webhook_not_found(self, service):
        """Test deleting non-existent webhook raises error."""
        with pytest.raises(ValueError, match="Webhook not found"):
            service.delete("nonexistent_id")

    def test_deactivate_webhook(self, service, sample_webhook):
        """Test deactivating a webhook."""
        service.deactivate(sample_webhook.id)
        assert service.get(sample_webhook.id).active is False

    def test_activate_webhook(self, service, sample_webhook):
        """Test activating an inactive webhook."""
        service.deactivate(sample_webhook.id)
        service.activate(sample_webhook.id)
        assert service.get(sample_webhook.id).active is True


# =============================================================================
# Test Event Types
# =============================================================================

class TestEventTypes:
    """Tests for supported event types."""

    def test_chat_completed_event(self, service):
        """Test chat.completed event is valid."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"]
        )
        assert "chat.completed" in webhook.events

    def test_escalation_created_event(self, service):
        """Test escalation.created event is valid."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["escalation.created"]
        )
        assert "escalation.created" in webhook.events

    def test_feedback_received_event(self, service):
        """Test feedback.received event is valid."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["feedback.received"]
        )
        assert "feedback.received" in webhook.events

    def test_conversation_started_event(self, service):
        """Test conversation.started event is valid."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["conversation.started"]
        )
        assert "conversation.started" in webhook.events

    def test_get_supported_events(self, service):
        """Test getting list of supported events."""
        events = service.get_supported_events()
        assert "chat.completed" in events
        assert "escalation.created" in events
        assert "feedback.received" in events
        assert "conversation.started" in events

    def test_wildcard_event_subscription(self, service):
        """Test subscribing to all events with wildcard."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["*"]
        )
        assert "*" in webhook.events


# =============================================================================
# Test Payload Signing (HMAC)
# =============================================================================

class TestPayloadSigning:
    """Tests for HMAC payload signing."""

    def test_sign_payload_basic(self, service):
        """Test basic payload signing."""
        payload = '{"event": "chat.completed"}'
        secret = "test_secret"
        signature = service.sign_payload(payload, secret)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length

    def test_sign_payload_produces_valid_hmac(self, service):
        """Test that signature is valid HMAC-SHA256."""
        payload = '{"event": "chat.completed"}'
        secret = "test_secret"
        signature = service.sign_payload(payload, secret)

        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        assert signature == expected

    def test_sign_payload_different_secrets(self, service):
        """Test that different secrets produce different signatures."""
        payload = '{"event": "chat.completed"}'
        sig1 = service.sign_payload(payload, "secret1")
        sig2 = service.sign_payload(payload, "secret2")
        assert sig1 != sig2

    def test_sign_payload_different_payloads(self, service):
        """Test that different payloads produce different signatures."""
        secret = "test_secret"
        sig1 = service.sign_payload('{"event": "chat.completed"}', secret)
        sig2 = service.sign_payload('{"event": "escalation.created"}', secret)
        assert sig1 != sig2

    def test_verify_signature_valid(self, service):
        """Test verifying a valid signature."""
        payload = '{"event": "chat.completed"}'
        secret = "test_secret"
        signature = service.sign_payload(payload, secret)

        assert service.verify_signature(payload, signature, secret) is True

    def test_verify_signature_invalid(self, service):
        """Test verifying an invalid signature."""
        payload = '{"event": "chat.completed"}'
        secret = "test_secret"

        assert service.verify_signature(payload, "invalid_signature", secret) is False

    def test_verify_signature_tampered_payload(self, service):
        """Test that tampered payload fails verification."""
        secret = "test_secret"
        original_payload = '{"event": "chat.completed"}'
        signature = service.sign_payload(original_payload, secret)

        tampered_payload = '{"event": "escalation.created"}'
        assert service.verify_signature(tampered_payload, signature, secret) is False

    def test_sign_payload_empty_string(self, service):
        """Test signing empty payload."""
        signature = service.sign_payload("", "secret")
        assert signature is not None

    def test_sign_payload_unicode(self, service):
        """Test signing payload with unicode characters."""
        payload = '{"message": "Hello"}'
        signature = service.sign_payload(payload, "secret")
        assert signature is not None


# =============================================================================
# Test Webhook Dispatching
# =============================================================================

class TestWebhookDispatching:
    """Tests for webhook event dispatching."""

    @pytest.mark.asyncio
    async def test_dispatch_creates_delivery(self, service, sample_webhook, sample_payload):
        """Test that dispatch creates a delivery record."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert len(deliveries) >= 1

    @pytest.mark.asyncio
    async def test_dispatch_only_to_subscribed_webhooks(self, service, sample_payload):
        """Test that dispatch only sends to webhooks subscribed to the event."""
        wh1 = service.register(url="https://example1.com/webhook", events=["chat.completed"])
        wh2 = service.register(url="https://example2.com/webhook", events=["escalation.created"])

        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            # Only wh1 should receive the event
            assert len(service.get_deliveries(wh1.id)) >= 1
            assert len(service.get_deliveries(wh2.id)) == 0

    @pytest.mark.asyncio
    async def test_dispatch_to_inactive_webhook_skipped(self, service, sample_webhook, sample_payload):
        """Test that dispatch skips inactive webhooks."""
        service.deactivate(sample_webhook.id)

        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            await service.dispatch("chat.completed", sample_payload)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_wildcard_subscription(self, service, sample_payload):
        """Test that wildcard subscription receives all events."""
        webhook = service.register(url="https://example.com/webhook", events=["*"])

        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)
            await service.dispatch("escalation.created", sample_payload)

            deliveries = service.get_deliveries(webhook.id)
            assert len(deliveries) >= 2

    @pytest.mark.asyncio
    async def test_dispatch_includes_signature_header(self, service, sample_webhook, sample_payload):
        """Test that dispatch includes signature in request."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            # Check that _send_webhook was called with signature
            call_args = mock_send.call_args
            assert 'signature' in call_args.kwargs or len(call_args.args) >= 4


# =============================================================================
# Test Retry Mechanism
# =============================================================================

class TestRetryMechanism:
    """Tests for webhook delivery retry mechanism."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, service, sample_webhook, sample_payload):
        """Test that failed deliveries are retried."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            # First call fails, second succeeds
            mock_send.side_effect = [(500, "Internal Server Error"), (200, "OK")]

            await service.dispatch("chat.completed", sample_payload)
            await service.retry_failed_deliveries()

            # Should have been called twice
            assert mock_send.call_count >= 2

    @pytest.mark.asyncio
    async def test_max_retry_attempts(self, service, sample_webhook, sample_payload):
        """Test that retries stop after max attempts."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (500, "Error")

            await service.dispatch("chat.completed", sample_payload)

            # Retry multiple times
            for _ in range(5):
                await service.retry_failed_deliveries()

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].attempts <= service.max_retry_attempts

    @pytest.mark.asyncio
    async def test_retry_increments_attempts(self, service, sample_webhook, sample_payload):
        """Test that each retry increments the attempts counter."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (500, "Error")

            await service.dispatch("chat.completed", sample_payload)
            initial_attempts = service.get_deliveries(sample_webhook.id)[0].attempts

            await service.retry_failed_deliveries()

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].attempts > initial_attempts

    @pytest.mark.asyncio
    async def test_successful_delivery_not_retried(self, service, sample_webhook, sample_payload):
        """Test that successful deliveries are not retried."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")

            await service.dispatch("chat.completed", sample_payload)

            # Clear mock call count
            mock_send.reset_mock()

            await service.retry_failed_deliveries()

            # Should not retry successful deliveries
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, service):
        """Test that retry uses exponential backoff."""
        # Verify backoff calculation
        delay1 = service.calculate_retry_delay(1)
        delay2 = service.calculate_retry_delay(2)
        delay3 = service.calculate_retry_delay(3)

        assert delay2 > delay1
        assert delay3 > delay2


# =============================================================================
# Test Delivery Status Tracking
# =============================================================================

class TestDeliveryStatusTracking:
    """Tests for webhook delivery status tracking."""

    @pytest.mark.asyncio
    async def test_delivery_status_pending(self, service, sample_webhook, sample_payload):
        """Test delivery starts with pending status."""
        delivery = service._create_delivery(sample_webhook.id, "chat.completed", sample_payload)
        assert delivery.status == DeliveryStatus.PENDING

    @pytest.mark.asyncio
    async def test_delivery_status_success(self, service, sample_webhook, sample_payload):
        """Test delivery status updates to success on 2xx response."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].status == DeliveryStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_delivery_status_failed(self, service, sample_webhook, sample_payload):
        """Test delivery status updates to failed on error response."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (500, "Internal Server Error")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].status == DeliveryStatus.FAILED

    @pytest.mark.asyncio
    async def test_delivery_response_code_stored(self, service, sample_webhook, sample_payload):
        """Test that response code is stored in delivery."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (201, "Created")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].response_code == 201

    @pytest.mark.asyncio
    async def test_get_deliveries_by_webhook(self, service, sample_webhook, sample_payload):
        """Test getting deliveries filtered by webhook ID."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert all(d.webhook_id == sample_webhook.id for d in deliveries)

    @pytest.mark.asyncio
    async def test_get_deliveries_by_status(self, service, sample_webhook, sample_payload):
        """Test getting deliveries filtered by status."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries_by_status(DeliveryStatus.SUCCESS)
            assert all(d.status == DeliveryStatus.SUCCESS for d in deliveries)

    def test_get_delivery_by_id(self, service, sample_webhook, sample_payload):
        """Test getting a specific delivery by ID."""
        delivery = service._create_delivery(sample_webhook.id, "chat.completed", sample_payload)
        service._deliveries.append(delivery)

        retrieved = service.get_delivery(delivery.id)
        assert retrieved.id == delivery.id

    @pytest.mark.asyncio
    async def test_delivery_timestamp_recorded(self, service, sample_webhook, sample_payload):
        """Test that delivery timestamp is recorded on success."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            deliveries = service.get_deliveries(sample_webhook.id)
            assert deliveries[0].delivered_at is not None


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_webhook_with_long_url(self, service):
        """Test webhook with very long URL."""
        long_url = "https://example.com/" + "a" * 500 + "/webhook"
        webhook = service.register(url=long_url, events=["chat.completed"])
        assert webhook.url == long_url

    def test_webhook_with_query_params_in_url(self, service):
        """Test webhook with query parameters in URL."""
        url = "https://example.com/webhook?key=value&token=abc"
        webhook = service.register(url=url, events=["chat.completed"])
        assert webhook.url == url

    @pytest.mark.asyncio
    async def test_dispatch_with_empty_payload(self, service, sample_webhook):
        """Test dispatch with empty payload."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", {})
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_with_large_payload(self, service, sample_webhook):
        """Test dispatch with large payload."""
        large_payload = {"data": "x" * 10000}
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", large_payload)
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_concurrent_events(self, service, sample_webhook, sample_payload):
        """Test dispatching multiple events concurrently."""
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")

            await asyncio.gather(
                service.dispatch("chat.completed", sample_payload),
                service.dispatch("chat.completed", sample_payload),
                service.dispatch("chat.completed", sample_payload)
            )

            assert mock_send.call_count >= 3

    def test_secret_generation_length(self, service):
        """Test that generated secrets have sufficient length."""
        secret = service._generate_secret()
        assert len(secret) >= 32

    def test_secret_generation_randomness(self, service):
        """Test that generated secrets are random."""
        secrets = [service._generate_secret() for _ in range(10)]
        assert len(set(secrets)) == 10  # All unique


# =============================================================================
# Test Webhook Service Singleton
# =============================================================================

class TestWebhookServiceSingleton:
    """Tests for the webhook service singleton instance."""

    def test_singleton_exists(self):
        """Test that singleton instance exists."""
        assert webhook_service is not None
        assert isinstance(webhook_service, WebhookService)

    def test_singleton_methods_accessible(self):
        """Test that singleton methods are accessible."""
        assert callable(webhook_service.register)
        assert callable(webhook_service.dispatch)
        assert callable(webhook_service.sign_payload)


# =============================================================================
# Integration Tests
# =============================================================================

class TestWebhookIntegration:
    """Integration tests for the complete webhook flow."""

    @pytest.mark.asyncio
    async def test_full_webhook_lifecycle(self, service):
        """Test complete webhook lifecycle: register, dispatch, deliver, track."""
        # Register webhook
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"],
            name="Test Webhook"
        )

        # Dispatch event
        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", {"conversation_id": "conv_123"})

        # Verify delivery
        deliveries = service.get_deliveries(webhook.id)
        assert len(deliveries) == 1
        assert deliveries[0].status == DeliveryStatus.SUCCESS

        # Deactivate webhook
        service.deactivate(webhook.id)
        assert service.get(webhook.id).active is False

        # Delete webhook
        service.delete(webhook.id)
        assert service.get(webhook.id) is None

    @pytest.mark.asyncio
    async def test_multiple_webhooks_same_event(self, service, sample_payload):
        """Test dispatching to multiple webhooks subscribed to same event."""
        wh1 = service.register(url="https://example1.com/webhook", events=["chat.completed"])
        wh2 = service.register(url="https://example2.com/webhook", events=["chat.completed"])
        wh3 = service.register(url="https://example3.com/webhook", events=["chat.completed"])

        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = (200, "OK")
            await service.dispatch("chat.completed", sample_payload)

            assert mock_send.call_count >= 3

    @pytest.mark.asyncio
    async def test_webhook_with_retry_flow(self, service, sample_payload):
        """Test webhook delivery with retry on failure."""
        webhook = service.register(
            url="https://example.com/webhook",
            events=["chat.completed"]
        )

        with patch.object(service, '_send_webhook', new_callable=AsyncMock) as mock_send:
            # First two calls fail, third succeeds
            mock_send.side_effect = [
                (500, "Error"),
                (500, "Error"),
                (200, "OK")
            ]

            await service.dispatch("chat.completed", sample_payload)

            # First delivery fails
            deliveries = service.get_deliveries(webhook.id)
            assert deliveries[0].status == DeliveryStatus.FAILED

            # Retry
            await service.retry_failed_deliveries()
            await service.retry_failed_deliveries()

            # Should eventually succeed
            deliveries = service.get_deliveries(webhook.id)
            assert deliveries[0].status == DeliveryStatus.SUCCESS
