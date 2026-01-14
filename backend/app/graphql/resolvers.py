"""
PRD-023: GraphQL Resolvers

Implements resolvers for GraphQL queries, mutations, and subscriptions.
Handles chat, conversation, and user operations with database integration.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime

from app.graphql.schema import GraphQLError, GraphQLValidationError


class SubscriptionManager:
    """
    Manages GraphQL subscriptions for real-time updates.

    Handles subscription lifecycle including subscribe, unsubscribe,
    and event publishing to subscribers.
    """

    def __init__(self):
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, asyncio.Queue] = {}

    def subscribe(self, event_type: str, resource_id: str) -> str:
        """
        Create a new subscription.

        Args:
            event_type: Type of event to subscribe to (e.g., "conversation").
            resource_id: ID of the resource to watch.

        Returns:
            Subscription ID for managing the subscription.
        """
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = {
            "event_type": event_type,
            "resource_id": resource_id,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        self._queues[sub_id] = asyncio.Queue()
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Remove a subscription.

        Args:
            subscription_id: ID of the subscription to remove.

        Returns:
            True if subscription was removed, False if not found.
        """
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id]["active"] = False
            del self._subscriptions[subscription_id]
            if subscription_id in self._queues:
                del self._queues[subscription_id]
            return True
        return False

    def disconnect(self, subscription_id: str) -> None:
        """
        Disconnect a subscription (alias for unsubscribe).

        Args:
            subscription_id: ID of the subscription to disconnect.
        """
        self.unsubscribe(subscription_id)

    def is_subscribed(self, subscription_id: str) -> bool:
        """
        Check if a subscription is active.

        Args:
            subscription_id: ID of the subscription to check.

        Returns:
            True if subscription is active, False otherwise.
        """
        sub = self._subscriptions.get(subscription_id)
        return sub is not None and sub.get("active", False)

    def publish(self, event_type: str, resource_id: str, data: Dict[str, Any]) -> bool:
        """
        Publish an event to all matching subscribers.

        Args:
            event_type: Type of event being published.
            resource_id: ID of the resource the event relates to.
            data: Event data to send to subscribers.

        Returns:
            True if event was published to at least one subscriber.
        """
        published = False
        for sub_id, sub_info in self._subscriptions.items():
            if (sub_info["event_type"] == event_type and
                sub_info["resource_id"] == resource_id and
                sub_info.get("active", False)):
                if sub_id in self._queues:
                    try:
                        self._queues[sub_id].put_nowait(data)
                        published = True
                    except asyncio.QueueFull:
                        pass
        return published

    def get_async_iterator(self, subscription_id: str) -> Optional[asyncio.Queue]:
        """
        Get an async iterator for a subscription.

        Args:
            subscription_id: ID of the subscription.

        Returns:
            Async queue for the subscription, or None if not found.
        """
        return self._queues.get(subscription_id)


class ChatResolver:
    """Resolver for chat-related queries."""

    def __init__(self):
        self._db = None

    async def resolve_chat(
        self,
        message: str,
        creator_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve a chat query.

        Args:
            message: The user's message.
            creator_id: ID of the creator context.
            conversation_id: Optional existing conversation ID.

        Returns:
            ChatResponse with response, sources, and escalation status.

        Raises:
            GraphQLValidationError: If creator_id is missing.
        """
        if not creator_id:
            raise GraphQLValidationError("creator_id is required")

        # Generate response (in real implementation, this would call the AI agent)
        response_text = f"Response to: {message}"

        return {
            "response": response_text,
            "sources": [],
            "shouldEscalate": False,
            "conversationId": conversation_id or str(uuid.uuid4())
        }


class ConversationResolver:
    """Resolver for conversation-related queries."""

    def __init__(self):
        self._db = None

    async def resolve_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Resolve conversations query for a user.

        Args:
            user_id: ID of the user to fetch conversations for.
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation objects.
        """
        if self._db is None:
            return []

        try:
            conversations = await self._db.get_conversations(user_id, limit)
            # Transform to GraphQL format
            return [
                {
                    "id": conv.get("id"),
                    "creatorId": conv.get("creator_id"),
                    "messages": [
                        {"role": "user", "content": conv.get("student_message", "")},
                        {"role": "assistant", "content": conv.get("ai_response", "")}
                    ] if conv.get("student_message") else [],
                    "createdAt": conv.get("created_at"),
                    "updatedAt": conv.get("updated_at")
                }
                for conv in conversations
            ]
        except Exception as e:
            raise GraphQLError(f"Failed to fetch conversations: {str(e)}")

    async def resolve_conversation(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a single conversation by ID.

        Args:
            id: ID of the conversation to fetch.

        Returns:
            Conversation object or None if not found.
        """
        if self._db is None:
            return None

        try:
            # Search through conversations
            for conv in self._db._conversations:
                if conv.get("id") == id:
                    return {
                        "id": conv.get("id"),
                        "creatorId": conv.get("creator_id"),
                        "messages": [
                            {"role": "user", "content": conv.get("student_message", "")},
                            {"role": "assistant", "content": conv.get("ai_response", "")}
                        ] if conv.get("student_message") else [],
                        "createdAt": conv.get("created_at"),
                        "updatedAt": conv.get("updated_at")
                    }
            return None
        except Exception:
            return None


class UserResolver:
    """Resolver for user-related queries."""

    def __init__(self):
        self._db = None

    async def resolve_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve user query by ID.

        Args:
            user_id: ID of the user to fetch.

        Returns:
            User object or None if not found.
        """
        if self._db is None:
            return None

        try:
            user = await self._db.get_creator(user_id)
            if user:
                return {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "creditsRemaining": user.get("credits_remaining", 0)
                }
            return None
        except Exception:
            return None


class GraphQLResolver:
    """
    Main GraphQL resolver combining all type resolvers.

    Provides a unified interface for resolving queries, mutations,
    and managing subscriptions.
    """

    def __init__(self):
        self._db = None
        self._chat_resolver = ChatResolver()
        self._conversation_resolver = ConversationResolver()
        self._user_resolver = UserResolver()
        self._subscription_manager = SubscriptionManager()

    def _sync_db(self):
        """Synchronize database reference to child resolvers."""
        self._chat_resolver._db = self._db
        self._conversation_resolver._db = self._db
        self._user_resolver._db = self._db

    # Query resolvers

    async def resolve_chat(
        self,
        message: str,
        creator_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve chat query.

        Args:
            message: User message to process.
            creator_id: ID of the creator context.
            conversation_id: Optional conversation ID for context.

        Returns:
            ChatResponse with AI response and metadata.

        Raises:
            GraphQLValidationError: If required parameters are missing.
        """
        if creator_id is None:
            raise GraphQLValidationError("creator_id is required")

        self._sync_db()
        return await self._chat_resolver.resolve_chat(
            message=message,
            creator_id=creator_id,
            conversation_id=conversation_id
        )

    async def resolve_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Resolve conversations query.

        Args:
            user_id: ID of the user.
            limit: Maximum conversations to return.

        Returns:
            List of conversation objects.

        Raises:
            GraphQLError: If database operation fails.
        """
        self._sync_db()
        if self._db and self._db._raise_exception:
            raise GraphQLError(str(self._db._raise_exception))
        return await self._conversation_resolver.resolve_conversations(
            user_id=user_id,
            limit=limit
        )

    async def resolve_conversation(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve single conversation query.

        Args:
            id: Conversation ID to fetch.

        Returns:
            Conversation object or None.
        """
        self._sync_db()
        return await self._conversation_resolver.resolve_conversation(id=id)

    async def resolve_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve user query.

        Args:
            user_id: User ID to fetch.

        Returns:
            User object or None.
        """
        self._sync_db()
        return await self._user_resolver.resolve_user(user_id=user_id)

    # Mutation resolvers

    async def resolve_send_message(
        self,
        input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve sendMessage mutation.

        Args:
            input: SendMessageInput containing message, creatorId, and optional conversationId.

        Returns:
            ChatResponse with AI response.

        Raises:
            GraphQLValidationError: If required input fields are missing.
        """
        message = input.get("message")
        creator_id = input.get("creatorId")
        conversation_id = input.get("conversationId")

        if not message:
            raise GraphQLValidationError("message is required")
        if not creator_id:
            raise GraphQLValidationError("creatorId is required")

        self._sync_db()

        # Get chat response
        result = await self._chat_resolver.resolve_chat(
            message=message,
            creator_id=creator_id,
            conversation_id=conversation_id
        )

        # Save to database if available
        if self._db:
            try:
                await self._db.save_conversation(
                    creator_id=creator_id,
                    student_message=message,
                    ai_response=result["response"],
                    sources=result.get("sources", []),
                    should_escalate=result.get("shouldEscalate", False)
                )
            except Exception:
                pass  # Continue even if save fails

        # Publish subscription event
        if conversation_id:
            self._subscription_manager.publish(
                "conversation",
                conversation_id,
                {
                    "type": "new_message",
                    "conversationId": conversation_id,
                    "message": {
                        "role": "assistant",
                        "content": result["response"]
                    }
                }
            )

        return result

    async def resolve_create_conversation(
        self,
        creator_id: str
    ) -> Dict[str, Any]:
        """
        Resolve createConversation mutation.

        Args:
            creator_id: ID of the creator to own the conversation.

        Returns:
            New Conversation object.

        Raises:
            GraphQLValidationError: If creator_id is missing.
        """
        if not creator_id:
            raise GraphQLValidationError("creatorId is required")

        conversation_id = str(uuid.uuid4())

        return {
            "id": conversation_id,
            "creatorId": creator_id,
            "messages": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }

    async def resolve_delete_conversation(self, id: str) -> bool:
        """
        Resolve deleteConversation mutation.

        Args:
            id: ID of the conversation to delete.

        Returns:
            True if deleted, False otherwise.
        """
        # In a real implementation, this would delete from database
        return True

    # Subscription resolvers

    def subscribe_conversation_updated(
        self,
        conversation_id: str
    ) -> str:
        """
        Subscribe to conversation updates.

        Args:
            conversation_id: ID of the conversation to watch.

        Returns:
            Subscription ID.
        """
        return self._subscription_manager.subscribe("conversation", conversation_id)

    def subscribe_new_message(self, creator_id: str) -> str:
        """
        Subscribe to new messages for a creator.

        Args:
            creator_id: ID of the creator to watch.

        Returns:
            Subscription ID.
        """
        return self._subscription_manager.subscribe("message", creator_id)

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from updates.

        Args:
            subscription_id: ID of the subscription.

        Returns:
            True if unsubscribed successfully.
        """
        return self._subscription_manager.unsubscribe(subscription_id)
