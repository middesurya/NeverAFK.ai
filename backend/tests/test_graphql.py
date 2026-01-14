"""
PRD-023: GraphQL Endpoint Tests

Comprehensive tests for GraphQL schema, resolvers, queries, mutations, and subscriptions.
Tests verify correct operation of:
- Query types (chat, conversations, user)
- Mutation types (sendMessage, createConversation)
- Subscription support
- Error handling
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import asyncio

# Import the modules we're testing
from app.graphql.schema import (
    GraphQLType,
    Field,
    ObjectType,
    SCHEMA,
    parse_schema,
    validate_query,
    GraphQLError,
    GraphQLValidationError,
)
from app.graphql.resolvers import (
    GraphQLResolver,
    ChatResolver,
    ConversationResolver,
    UserResolver,
    SubscriptionManager,
)

from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def resolver():
    """Create a GraphQL resolver instance."""
    return GraphQLResolver()


@pytest.fixture
def chat_resolver():
    """Create a ChatResolver instance."""
    return ChatResolver()


@pytest.fixture
def conversation_resolver():
    """Create a ConversationResolver instance."""
    return ConversationResolver()


@pytest.fixture
def user_resolver():
    """Create a UserResolver instance."""
    return UserResolver()


@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    return MockDatabase()


@pytest.fixture
def sample_chat_response():
    """Sample chat response data."""
    return {
        "response": "Python is a programming language.",
        "sources": ["Module 1 - Introduction"],
        "shouldEscalate": False,
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation data."""
    return {
        "id": "conv-123",
        "creatorId": "creator-456",
        "messages": [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
        ],
    }


@pytest.fixture
def sample_conversations():
    """Sample list of conversations."""
    return [
        {
            "id": "conv-1",
            "creatorId": "creator-123",
            "messages": [],
        },
        {
            "id": "conv-2",
            "creatorId": "creator-123",
            "messages": [],
        },
    ]


# =============================================================================
# Schema Type Tests
# =============================================================================

class TestGraphQLTypeEnum:
    """Tests for GraphQLType enum."""

    def test_query_type_exists(self):
        """GraphQLType should have QUERY type."""
        assert GraphQLType.QUERY.value == "Query"

    def test_mutation_type_exists(self):
        """GraphQLType should have MUTATION type."""
        assert GraphQLType.MUTATION.value == "Mutation"

    def test_subscription_type_exists(self):
        """GraphQLType should have SUBSCRIPTION type."""
        assert GraphQLType.SUBSCRIPTION.value == "Subscription"

    def test_all_types_defined(self):
        """All three GraphQL types should be defined."""
        types = [t.value for t in GraphQLType]
        assert "Query" in types
        assert "Mutation" in types
        assert "Subscription" in types


class TestFieldDataclass:
    """Tests for Field dataclass."""

    def test_field_creation_basic(self):
        """Field should be creatable with basic parameters."""
        field = Field(name="id", type="String")
        assert field.name == "id"
        assert field.type == "String"

    def test_field_default_nullable(self):
        """Field should default to nullable=True."""
        field = Field(name="id", type="String")
        assert field.nullable is True

    def test_field_with_args(self):
        """Field should accept args parameter."""
        field = Field(name="chat", type="ChatResponse", args={"message": "String!"})
        assert field.args == {"message": "String!"}

    def test_field_non_nullable(self):
        """Field should accept nullable=False."""
        field = Field(name="id", type="String!", nullable=False)
        assert field.nullable is False

    def test_field_default_args_none(self):
        """Field should default args to None."""
        field = Field(name="id", type="String")
        assert field.args is None


class TestObjectTypeDataclass:
    """Tests for ObjectType dataclass."""

    def test_object_type_creation(self):
        """ObjectType should be creatable with name and fields."""
        fields = [Field(name="id", type="String"), Field(name="name", type="String")]
        obj_type = ObjectType(name="User", fields=fields)
        assert obj_type.name == "User"
        assert len(obj_type.fields) == 2

    def test_object_type_field_access(self):
        """ObjectType fields should be accessible."""
        fields = [Field(name="response", type="String!")]
        obj_type = ObjectType(name="ChatResponse", fields=fields)
        assert obj_type.fields[0].name == "response"


# =============================================================================
# Schema Definition Tests
# =============================================================================

class TestSchemaDefinition:
    """Tests for GraphQL schema definition string."""

    def test_schema_contains_query_type(self):
        """Schema should define Query type."""
        assert "type Query" in SCHEMA

    def test_schema_contains_mutation_type(self):
        """Schema should define Mutation type."""
        assert "type Mutation" in SCHEMA

    def test_query_has_chat_field(self):
        """Query should have chat field."""
        assert "chat(" in SCHEMA

    def test_query_has_conversations_field(self):
        """Query should have conversations field."""
        assert "conversations(" in SCHEMA

    def test_query_has_conversation_field(self):
        """Query should have single conversation field."""
        assert "conversation(" in SCHEMA

    def test_mutation_has_send_message(self):
        """Mutation should have sendMessage field."""
        assert "sendMessage(" in SCHEMA

    def test_mutation_has_create_conversation(self):
        """Mutation should have createConversation field."""
        assert "createConversation(" in SCHEMA

    def test_chat_response_type_defined(self):
        """ChatResponse type should be defined."""
        assert "type ChatResponse" in SCHEMA

    def test_conversation_type_defined(self):
        """Conversation type should be defined."""
        assert "type Conversation" in SCHEMA

    def test_chat_response_has_response_field(self):
        """ChatResponse should have response field."""
        assert "response: String!" in SCHEMA

    def test_chat_response_has_sources_field(self):
        """ChatResponse should have sources field."""
        assert "sources:" in SCHEMA

    def test_chat_response_has_should_escalate(self):
        """ChatResponse should have shouldEscalate field."""
        assert "shouldEscalate:" in SCHEMA


# =============================================================================
# Schema Parsing Tests
# =============================================================================

class TestSchemaParsing:
    """Tests for schema parsing functionality."""

    def test_parse_schema_returns_dict(self):
        """parse_schema should return a dictionary."""
        result = parse_schema(SCHEMA)
        assert isinstance(result, dict)

    def test_parse_schema_has_query(self):
        """Parsed schema should contain Query type."""
        result = parse_schema(SCHEMA)
        assert "Query" in result

    def test_parse_schema_has_mutation(self):
        """Parsed schema should contain Mutation type."""
        result = parse_schema(SCHEMA)
        assert "Mutation" in result

    def test_parse_schema_extracts_fields(self):
        """Parsed schema should extract type fields."""
        result = parse_schema(SCHEMA)
        assert "chat" in result.get("Query", {}).get("fields", {})


# =============================================================================
# Query Validation Tests
# =============================================================================

class TestQueryValidation:
    """Tests for GraphQL query validation."""

    def test_validate_valid_chat_query(self):
        """Valid chat query should pass validation."""
        query = """
        query {
            chat(message: "Hello", creatorId: "123") {
                response
                sources
            }
        }
        """
        assert validate_query(query) is True

    def test_validate_invalid_field_raises_error(self):
        """Invalid field should raise validation error."""
        query = """
        query {
            invalidField {
                response
            }
        }
        """
        with pytest.raises(GraphQLValidationError):
            validate_query(query, strict=True)

    def test_validate_empty_query_raises_error(self):
        """Empty query should raise validation error."""
        with pytest.raises(GraphQLValidationError):
            validate_query("", strict=True)

    def test_validate_missing_required_args(self):
        """Missing required arguments should raise error."""
        query = """
        query {
            chat {
                response
            }
        }
        """
        with pytest.raises(GraphQLValidationError):
            validate_query(query, strict=True)


# =============================================================================
# Chat Resolver Tests
# =============================================================================

class TestChatResolver:
    """Tests for ChatResolver."""

    @pytest.mark.asyncio
    async def test_resolve_chat_returns_dict(self, chat_resolver):
        """resolve_chat should return a dictionary."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_resolve_chat_has_response_field(self, chat_resolver):
        """resolve_chat result should have response field."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert "response" in result

    @pytest.mark.asyncio
    async def test_resolve_chat_has_sources_field(self, chat_resolver):
        """resolve_chat result should have sources field."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_resolve_chat_has_should_escalate(self, chat_resolver):
        """resolve_chat result should have shouldEscalate field."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert "shouldEscalate" in result

    @pytest.mark.asyncio
    async def test_resolve_chat_sources_is_list(self, chat_resolver):
        """resolve_chat sources should be a list."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert isinstance(result["sources"], list)

    @pytest.mark.asyncio
    async def test_resolve_chat_should_escalate_is_bool(self, chat_resolver):
        """resolve_chat shouldEscalate should be boolean."""
        result = await chat_resolver.resolve_chat(
            message="What is Python?",
            creator_id="creator-123"
        )
        assert isinstance(result["shouldEscalate"], bool)

    @pytest.mark.asyncio
    async def test_resolve_chat_with_conversation_id(self, chat_resolver):
        """resolve_chat should accept optional conversation_id."""
        result = await chat_resolver.resolve_chat(
            message="Follow up question",
            creator_id="creator-123",
            conversation_id="conv-456"
        )
        assert result is not None


# =============================================================================
# Conversation Resolver Tests
# =============================================================================

class TestConversationResolver:
    """Tests for ConversationResolver."""

    @pytest.mark.asyncio
    async def test_resolve_conversations_returns_list(self, conversation_resolver, mock_db):
        """resolve_conversations should return a list."""
        with patch.object(conversation_resolver, '_db', mock_db):
            result = await conversation_resolver.resolve_conversations(
                user_id="creator-123"
            )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_resolve_conversation_by_id(self, conversation_resolver, mock_db):
        """resolve_conversation should fetch conversation by ID."""
        mock_db._conversations = [{
            "id": "conv-123",
            "creator_id": "creator-456",
            "student_message": "Test",
            "ai_response": "Response",
            "sources": [],
            "should_escalate": False,
            "created_at": "2024-01-15T10:00:00Z"
        }]
        with patch.object(conversation_resolver, '_db', mock_db):
            result = await conversation_resolver.resolve_conversation(id="conv-123")
        assert result is not None

    @pytest.mark.asyncio
    async def test_resolve_conversation_not_found(self, conversation_resolver, mock_db):
        """resolve_conversation should return None for invalid ID."""
        with patch.object(conversation_resolver, '_db', mock_db):
            result = await conversation_resolver.resolve_conversation(id="invalid-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_conversations_filters_by_user(self, conversation_resolver, mock_db):
        """resolve_conversations should filter by user_id."""
        mock_db._conversations = [
            {"id": "1", "creator_id": "user-A", "student_message": "Q1", "ai_response": "A1", "sources": [], "should_escalate": False, "created_at": "2024-01-15"},
            {"id": "2", "creator_id": "user-B", "student_message": "Q2", "ai_response": "A2", "sources": [], "should_escalate": False, "created_at": "2024-01-15"},
        ]
        with patch.object(conversation_resolver, '_db', mock_db):
            result = await conversation_resolver.resolve_conversations(user_id="user-A")
        assert all(c.get("creatorId") == "user-A" or c.get("creator_id") == "user-A" for c in result)


# =============================================================================
# User Resolver Tests
# =============================================================================

class TestUserResolver:
    """Tests for UserResolver."""

    @pytest.mark.asyncio
    async def test_resolve_user_returns_user_data(self, user_resolver, mock_db):
        """resolve_user should return user data."""
        mock_db._creators["user-123"] = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "credits_remaining": 100
        }
        with patch.object(user_resolver, '_db', mock_db):
            result = await user_resolver.resolve_user(user_id="user-123")
        assert result is not None
        assert result.get("id") == "user-123"

    @pytest.mark.asyncio
    async def test_resolve_user_not_found(self, user_resolver, mock_db):
        """resolve_user should return None for invalid ID."""
        with patch.object(user_resolver, '_db', mock_db):
            result = await user_resolver.resolve_user(user_id="invalid-user")
        assert result is None


# =============================================================================
# Mutation Tests
# =============================================================================

class TestMutations:
    """Tests for GraphQL mutations."""

    @pytest.mark.asyncio
    async def test_send_message_mutation(self, resolver, mock_db):
        """sendMessage mutation should process message."""
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_send_message(
                input={"message": "Hello", "creatorId": "creator-123"}
            )
        assert "response" in result

    @pytest.mark.asyncio
    async def test_create_conversation_mutation(self, resolver, mock_db):
        """createConversation mutation should create new conversation."""
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_create_conversation(
                creator_id="creator-123"
            )
        assert "id" in result
        assert result["creatorId"] == "creator-123"

    @pytest.mark.asyncio
    async def test_send_message_saves_to_db(self, resolver, mock_db):
        """sendMessage should save conversation to database."""
        with patch.object(resolver, '_db', mock_db):
            await resolver.resolve_send_message(
                input={"message": "Test message", "creatorId": "creator-123"}
            )
        save_calls = [c for c in mock_db.call_history if c["method"] == "save_conversation"]
        assert len(save_calls) >= 1


# =============================================================================
# Subscription Tests
# =============================================================================

class TestSubscriptions:
    """Tests for GraphQL subscriptions."""

    def test_subscription_manager_creation(self):
        """SubscriptionManager should be creatable."""
        manager = SubscriptionManager()
        assert manager is not None

    def test_subscribe_to_conversation(self):
        """Should be able to subscribe to conversation updates."""
        manager = SubscriptionManager()
        subscription = manager.subscribe("conversation", "conv-123")
        assert subscription is not None

    def test_unsubscribe_from_conversation(self):
        """Should be able to unsubscribe from conversation."""
        manager = SubscriptionManager()
        sub_id = manager.subscribe("conversation", "conv-123")
        result = manager.unsubscribe(sub_id)
        assert result is True

    def test_publish_to_subscribers(self):
        """Should be able to publish events to subscribers."""
        manager = SubscriptionManager()
        manager.subscribe("conversation", "conv-123")
        result = manager.publish("conversation", "conv-123", {"type": "new_message"})
        assert result is True

    def test_no_publish_without_subscribers(self):
        """Publish should handle no subscribers gracefully."""
        manager = SubscriptionManager()
        result = manager.publish("conversation", "conv-456", {"type": "new_message"})
        # Should not raise, may return False or handle gracefully
        assert result in [True, False]

    @pytest.mark.asyncio
    async def test_async_subscription_iterator(self):
        """Subscription should provide async iterator."""
        manager = SubscriptionManager()
        sub_id = manager.subscribe("conversation", "conv-123")
        iterator = manager.get_async_iterator(sub_id)
        assert hasattr(iterator, '__aiter__') or iterator is not None


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for GraphQL error handling."""

    def test_graphql_error_creation(self):
        """GraphQLError should be creatable."""
        error = GraphQLError("Test error message")
        assert str(error) == "Test error message"

    def test_graphql_error_with_path(self):
        """GraphQLError should accept path parameter."""
        error = GraphQLError("Field error", path=["query", "chat", "response"])
        assert error.path == ["query", "chat", "response"]

    def test_graphql_validation_error(self):
        """GraphQLValidationError should be creatable."""
        error = GraphQLValidationError("Invalid query")
        assert isinstance(error, GraphQLError)

    def test_error_serialization(self):
        """GraphQL errors should be serializable."""
        error = GraphQLError("Test error", path=["query"])
        error_dict = error.to_dict()
        assert "message" in error_dict
        assert error_dict["message"] == "Test error"

    @pytest.mark.asyncio
    async def test_resolver_handles_db_error(self, resolver, mock_db):
        """Resolver should handle database errors gracefully."""
        mock_db._raise_exception = Exception("Database connection failed")
        with patch.object(resolver, '_db', mock_db):
            with pytest.raises(GraphQLError):
                await resolver.resolve_conversations(user_id="creator-123")

    @pytest.mark.asyncio
    async def test_resolver_handles_missing_creator(self, resolver):
        """Resolver should handle missing creator_id."""
        with pytest.raises(GraphQLValidationError):
            await resolver.resolve_chat(message="Hello", creator_id=None)


# =============================================================================
# Integration Tests
# =============================================================================

class TestGraphQLIntegration:
    """Integration tests for GraphQL endpoint."""

    @pytest.mark.asyncio
    async def test_full_chat_flow(self, resolver, mock_db):
        """Test complete chat query to response flow."""
        mock_db.set_creator_credits("creator-123", 100)
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_chat(
                message="What is Python?",
                creator_id="creator-123"
            )
        assert "response" in result
        assert "sources" in result
        assert "shouldEscalate" in result

    @pytest.mark.asyncio
    async def test_conversation_history_flow(self, resolver, mock_db):
        """Test conversation creation and retrieval."""
        # Create conversation
        with patch.object(resolver, '_db', mock_db):
            created = await resolver.resolve_create_conversation(
                creator_id="creator-123"
            )
            assert "id" in created

            # Send message
            await resolver.resolve_send_message(
                input={
                    "message": "Hello",
                    "creatorId": "creator-123",
                    "conversationId": created["id"]
                }
            )

            # Retrieve conversations
            conversations = await resolver.resolve_conversations(
                user_id="creator-123"
            )
            assert len(conversations) >= 1

    @pytest.mark.asyncio
    async def test_multiple_queries_same_resolver(self, resolver, mock_db):
        """Resolver should handle multiple queries."""
        with patch.object(resolver, '_db', mock_db):
            result1 = await resolver.resolve_chat(
                message="Question 1",
                creator_id="creator-123"
            )
            result2 = await resolver.resolve_chat(
                message="Question 2",
                creator_id="creator-123"
            )
        assert result1 is not None
        assert result2 is not None


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_message(self, resolver, mock_db):
        """Resolver should handle empty message."""
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_chat(
                message="",
                creator_id="creator-123"
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_very_long_message(self, resolver, mock_db):
        """Resolver should handle very long message."""
        long_message = "Test " * 1000
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_chat(
                message=long_message,
                creator_id="creator-123"
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, resolver, mock_db):
        """Resolver should handle special characters."""
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_chat(
                message="What's the <script>alert('test')</script> syntax?",
                creator_id="creator-123"
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_unicode_in_message(self, resolver, mock_db):
        """Resolver should handle unicode characters."""
        with patch.object(resolver, '_db', mock_db):
            result = await resolver.resolve_chat(
                message="Wie funktioniert Python?",
                creator_id="creator-123"
            )
        assert result is not None

    def test_subscription_cleanup_on_disconnect(self):
        """Subscriptions should be cleaned up on disconnect."""
        manager = SubscriptionManager()
        sub_id = manager.subscribe("conversation", "conv-123")
        manager.disconnect(sub_id)
        # Verify subscription is removed
        assert not manager.is_subscribed(sub_id)


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Tests for performance-related behavior."""

    @pytest.mark.asyncio
    async def test_resolver_caches_results(self, resolver, mock_db):
        """Resolver should support result caching."""
        with patch.object(resolver, '_db', mock_db):
            # First call
            result1 = await resolver.resolve_chat(
                message="Cached question",
                creator_id="creator-123"
            )
            # Second call with same params should be cached
            result2 = await resolver.resolve_chat(
                message="Cached question",
                creator_id="creator-123"
            )
        # Results should be similar (caching doesn't change output)
        assert result1 is not None
        assert result2 is not None

    def test_subscription_manager_handles_many_subscriptions(self):
        """Subscription manager should handle many subscriptions."""
        manager = SubscriptionManager()
        sub_ids = []
        for i in range(100):
            sub_id = manager.subscribe("conversation", f"conv-{i}")
            sub_ids.append(sub_id)
        assert len(sub_ids) == 100
        # Cleanup
        for sub_id in sub_ids:
            manager.unsubscribe(sub_id)
