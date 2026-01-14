"""
Webhook API endpoints for managing webhooks and viewing deliveries.

Provides:
- POST /webhooks - Register a new webhook
- GET /webhooks - List all webhooks
- GET /webhooks/{webhook_id} - Get a specific webhook
- PATCH /webhooks/{webhook_id} - Update a webhook
- DELETE /webhooks/{webhook_id} - Delete a webhook
- POST /webhooks/{webhook_id}/activate - Activate a webhook
- POST /webhooks/{webhook_id}/deactivate - Deactivate a webhook
- GET /webhooks/{webhook_id}/deliveries - Get deliveries for a webhook
- GET /webhooks/deliveries/{delivery_id} - Get a specific delivery
- GET /webhooks/events - Get list of supported events
- POST /webhooks/test/{webhook_id} - Send a test event to a webhook

PRD-024: Webhook System API Endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional
from datetime import datetime

from app.services.webhook_service import (
    webhook_service,
    Webhook,
    WebhookDelivery,
    DeliveryStatus,
    VALID_EVENT_TYPES,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# =============================================================================
# Request/Response Models
# =============================================================================

class WebhookCreateRequest(BaseModel):
    """Request model for creating a webhook."""
    url: str = Field(..., description="The URL to send webhook events to")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    name: Optional[str] = Field(None, description="Human-readable name for the webhook")
    description: Optional[str] = Field(None, description="Description of the webhook's purpose")

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('events')
    def validate_events(cls, v):
        if not v:
            raise ValueError('At least one event type is required')
        for event in v:
            if event not in VALID_EVENT_TYPES:
                raise ValueError(f'Invalid event type: {event}')
        return v


class WebhookUpdateRequest(BaseModel):
    """Request model for updating a webhook."""
    url: Optional[str] = Field(None, description="The URL to send webhook events to")
    events: Optional[List[str]] = Field(None, description="List of event types to subscribe to")
    active: Optional[bool] = Field(None, description="Whether the webhook is active")
    name: Optional[str] = Field(None, description="Human-readable name for the webhook")
    description: Optional[str] = Field(None, description="Description of the webhook's purpose")

    @validator('url')
    def validate_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('events')
    def validate_events(cls, v):
        if v is not None:
            if not v:
                raise ValueError('At least one event type is required')
            for event in v:
                if event not in VALID_EVENT_TYPES:
                    raise ValueError(f'Invalid event type: {event}')
        return v


class WebhookResponse(BaseModel):
    """Response model for a webhook."""
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    name: Optional[str] = None
    description: Optional[str] = None
    secret: Optional[str] = None  # Only included on creation


class WebhookListResponse(BaseModel):
    """Response model for listing webhooks."""
    webhooks: List[WebhookResponse]
    total: int


class DeliveryResponse(BaseModel):
    """Response model for a delivery."""
    id: str
    webhook_id: str
    event: str
    payload: dict
    status: str
    attempts: int
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: str
    delivered_at: Optional[str] = None


class DeliveryListResponse(BaseModel):
    """Response model for listing deliveries."""
    deliveries: List[DeliveryResponse]
    total: int


class EventsResponse(BaseModel):
    """Response model for supported events."""
    events: List[str]


class TestWebhookRequest(BaseModel):
    """Request model for testing a webhook."""
    event: str = Field(default="chat.completed", description="Event type to test with")
    payload: Optional[dict] = Field(default=None, description="Custom payload for the test")


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# =============================================================================
# Helper Functions
# =============================================================================

def webhook_to_response(webhook: Webhook, include_secret: bool = False) -> WebhookResponse:
    """Convert a Webhook object to a response model."""
    return WebhookResponse(
        id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        active=webhook.active,
        created_at=webhook.created_at.isoformat(),
        name=webhook.name,
        description=webhook.description,
        secret=webhook.secret if include_secret else None
    )


def delivery_to_response(delivery: WebhookDelivery) -> DeliveryResponse:
    """Convert a WebhookDelivery object to a response model."""
    return DeliveryResponse(
        id=delivery.id,
        webhook_id=delivery.webhook_id,
        event=delivery.event,
        payload=delivery.payload,
        status=delivery.status.value,
        attempts=delivery.attempts,
        response_code=delivery.response_code,
        response_body=delivery.response_body,
        created_at=delivery.created_at.isoformat(),
        delivered_at=delivery.delivered_at.isoformat() if delivery.delivered_at else None
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(request: WebhookCreateRequest):
    """
    Register a new webhook.

    Creates a new webhook subscription for the specified events.
    Returns the webhook details including the secret key for signature verification.

    The secret is only returned on creation - store it securely.
    """
    try:
        webhook = webhook_service.register(
            url=request.url,
            events=request.events,
            name=request.name,
            description=request.description
        )
        return webhook_to_response(webhook, include_secret=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    active_only: bool = Query(False, description="Filter to only active webhooks")
):
    """
    List all registered webhooks.

    Returns a list of all webhooks. Optionally filter to only active webhooks.
    """
    webhooks = webhook_service.list()
    if active_only:
        webhooks = [w for w in webhooks if w.active]

    return WebhookListResponse(
        webhooks=[webhook_to_response(w) for w in webhooks],
        total=len(webhooks)
    )


@router.get("/events", response_model=EventsResponse)
async def get_supported_events():
    """
    Get list of supported event types.

    Returns all event types that can be subscribed to.
    """
    events = webhook_service.get_supported_events()
    return EventsResponse(events=events)


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str):
    """
    Get a specific webhook by ID.

    Returns the webhook details for the given ID.
    """
    webhook = webhook_service.get(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook not found: {webhook_id}"
        )
    return webhook_to_response(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: str, request: WebhookUpdateRequest):
    """
    Update a webhook.

    Updates the webhook configuration with the provided values.
    Only provided fields will be updated.
    """
    try:
        webhook = webhook_service.update(
            webhook_id=webhook_id,
            url=request.url,
            events=request.events,
            active=request.active,
            name=request.name,
            description=request.description
        )
        return webhook_to_response(webhook)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: str):
    """
    Delete a webhook.

    Permanently deletes the webhook and all its delivery history.
    """
    try:
        webhook_service.delete(webhook_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{webhook_id}/activate", response_model=MessageResponse)
async def activate_webhook(webhook_id: str):
    """
    Activate a webhook.

    Re-enables delivery of events to a previously deactivated webhook.
    """
    try:
        webhook_service.activate(webhook_id)
        return MessageResponse(message=f"Webhook {webhook_id} activated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{webhook_id}/deactivate", response_model=MessageResponse)
async def deactivate_webhook(webhook_id: str):
    """
    Deactivate a webhook.

    Temporarily stops delivery of events to the webhook without deleting it.
    """
    try:
        webhook_service.deactivate(webhook_id)
        return MessageResponse(message=f"Webhook {webhook_id} deactivated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{webhook_id}/deliveries", response_model=DeliveryListResponse)
async def get_webhook_deliveries(
    webhook_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, success, failed)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of deliveries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get deliveries for a webhook.

    Returns the delivery history for a specific webhook.
    """
    # Verify webhook exists
    webhook = webhook_service.get(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook not found: {webhook_id}"
        )

    deliveries = webhook_service.get_deliveries(webhook_id)

    # Filter by status if provided
    if status_filter:
        try:
            status_enum = DeliveryStatus(status_filter)
            deliveries = [d for d in deliveries if d.status == status_enum]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: pending, success, failed"
            )

    # Sort by created_at descending
    deliveries = sorted(deliveries, key=lambda d: d.created_at, reverse=True)

    # Apply pagination
    total = len(deliveries)
    deliveries = deliveries[offset:offset + limit]

    return DeliveryListResponse(
        deliveries=[delivery_to_response(d) for d in deliveries],
        total=total
    )


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: str):
    """
    Get a specific delivery by ID.

    Returns the delivery details including status and response information.
    """
    delivery = webhook_service.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery not found: {delivery_id}"
        )
    return delivery_to_response(delivery)


@router.post("/{webhook_id}/test", response_model=MessageResponse)
async def test_webhook(
    webhook_id: str,
    request: TestWebhookRequest,
    background_tasks: BackgroundTasks
):
    """
    Send a test event to a webhook.

    Sends a test event to verify the webhook is correctly configured.
    The delivery happens in the background.
    """
    webhook = webhook_service.get(webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook not found: {webhook_id}"
        )

    # Validate event type
    if request.event not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {request.event}"
        )

    # Default test payload
    test_payload = request.payload or {
        "test": True,
        "message": "This is a test webhook delivery",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Dispatch in background
    async def send_test():
        await webhook_service.dispatch(request.event, test_payload)

    background_tasks.add_task(send_test)

    return MessageResponse(
        message=f"Test event '{request.event}' queued for delivery to webhook {webhook_id}"
    )


@router.post("/retry-failed", response_model=MessageResponse)
async def retry_failed_deliveries(background_tasks: BackgroundTasks):
    """
    Retry all failed deliveries.

    Queues retry attempts for all failed deliveries that haven't exceeded max attempts.
    """
    async def do_retry():
        count = await webhook_service.retry_failed_deliveries()
        return count

    background_tasks.add_task(do_retry)

    return MessageResponse(message="Failed deliveries queued for retry")
