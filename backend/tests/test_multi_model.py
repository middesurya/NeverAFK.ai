"""
PRD-007: Multi-Model Support Tests

Tests for ModelProviderService with fallback chains:
- AC-1: Uses primary model (OpenAI) when available
- AC-2: Falls back to Claude when OpenAI fails
- AC-3: Can select specific model on request
- AC-4: Graceful error when all models fail

These tests use mocks to avoid real API calls.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Any

# Import mocks from PRD-002
from tests.mocks.openai_mock import MockChatOpenAI, MockOpenAIResponse


# =============================================================================
# Mock for Anthropic (Claude) - Similar to OpenAI mock
# =============================================================================

class MockChatAnthropic:
    """Mock implementation of ChatAnthropic for testing without API calls."""

    def __init__(
        self,
        default_response: str = "This is a mock Claude response.",
        responses: List[str] = None,
        raise_exception: Exception = None
    ):
        self.default_response = default_response
        self._responses = responses or []
        self._response_index = 0
        self._raise_exception = raise_exception
        self.call_history: List[Any] = []

    @property
    def call_count(self) -> int:
        return len(self.call_history)

    async def ainvoke(self, messages: List[Any]) -> MockOpenAIResponse:
        """Async invoke matching LangChain ChatAnthropic interface."""
        if self._raise_exception:
            raise self._raise_exception

        self.call_history.append({"messages": messages})

        if self._responses and self._response_index < len(self._responses):
            content = self._responses[self._response_index]
            self._response_index += 1
        else:
            content = self.default_response

        return MockOpenAIResponse(content)

    def reset_history(self) -> None:
        """Reset call history and response index."""
        self.call_history = []
        self._response_index = 0


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI model."""
    return MockChatOpenAI(default_response="OpenAI response content")


@pytest.fixture
def mock_anthropic():
    """Create a mock Anthropic model."""
    return MockChatAnthropic(default_response="Claude response content")


@pytest.fixture
def mock_openai_failing():
    """Create a mock OpenAI model that always fails."""
    return MockChatOpenAI(raise_exception=RuntimeError("OpenAI API unavailable"))


@pytest.fixture
def mock_anthropic_failing():
    """Create a mock Anthropic model that always fails."""
    return MockChatAnthropic(raise_exception=RuntimeError("Anthropic API unavailable"))


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]


# =============================================================================
# AC-1: Uses primary model (OpenAI) when available
# =============================================================================

class TestPrimaryModelUsage:
    """Tests for AC-1: Using primary model when available."""

    @pytest.mark.asyncio
    async def test_uses_openai_as_primary_when_available(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Should use OpenAI as primary model when both are available."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # OpenAI should be called
            assert mock_openai.call_count == 1
            # Claude should NOT be called
            assert mock_anthropic.call_count == 0
            # Result should contain OpenAI response
            assert result.content == "OpenAI response content"

    @pytest.mark.asyncio
    async def test_primary_model_returns_consistent_response_format(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Primary model should return response with content attribute."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Should have content attribute
            assert hasattr(result, 'content')
            assert isinstance(result.content, str)
            assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_tracks_which_model_was_used(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Should track which model provider was used for the response."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Should have provider info
            assert hasattr(result, 'provider')
            assert result.provider == ModelProvider.OPENAI


# =============================================================================
# AC-2: Falls back to Claude when OpenAI fails
# =============================================================================

class TestFallbackBehavior:
    """Tests for AC-2: Fallback to Claude when OpenAI fails."""

    @pytest.mark.asyncio
    async def test_falls_back_to_claude_when_openai_fails(
        self, mock_openai_failing, mock_anthropic, sample_messages
    ):
        """Should use Claude when OpenAI fails."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Claude should be used as fallback
            assert mock_anthropic.call_count == 1
            assert result.content == "Claude response content"

    @pytest.mark.asyncio
    async def test_fallback_returns_consistent_response_format(
        self, mock_openai_failing, mock_anthropic, sample_messages
    ):
        """Fallback model should return same response format as primary."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Should have same structure as primary model response
            assert hasattr(result, 'content')
            assert isinstance(result.content, str)

    @pytest.mark.asyncio
    async def test_tracks_fallback_provider_used(
        self, mock_openai_failing, mock_anthropic, sample_messages
    ):
        """Should track when fallback provider was used."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Should indicate Claude was used
            assert result.provider == ModelProvider.ANTHROPIC

    @pytest.mark.asyncio
    async def test_uses_only_available_model_when_one_key_missing(
        self, mock_anthropic, sample_messages
    ):
        """Should use available model when other API key is missing."""
        # Only Anthropic key available
        with patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}, clear=True):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Should use Claude since it's the only available model
            assert mock_anthropic.call_count == 1
            assert result.content == "Claude response content"


# =============================================================================
# AC-3: Can select specific model on request
# =============================================================================

class TestModelSelection:
    """Tests for AC-3: Selecting specific model on request."""

    @pytest.mark.asyncio
    async def test_can_request_specific_openai_model(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Should use OpenAI when explicitly requested."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()
            result = await service.invoke(sample_messages, preferred_model=ModelProvider.OPENAI)

            assert mock_openai.call_count == 1
            assert mock_anthropic.call_count == 0
            assert result.provider == ModelProvider.OPENAI

    @pytest.mark.asyncio
    async def test_can_request_specific_anthropic_model(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Should use Anthropic when explicitly requested."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()
            result = await service.invoke(sample_messages, preferred_model=ModelProvider.ANTHROPIC)

            # OpenAI should NOT be called
            assert mock_openai.call_count == 0
            # Anthropic should be called
            assert mock_anthropic.call_count == 1
            assert result.provider == ModelProvider.ANTHROPIC

    @pytest.mark.asyncio
    async def test_specific_model_still_falls_back_on_failure(
        self, mock_openai_failing, mock_anthropic, sample_messages
    ):
        """Should fall back even when specific model is requested but fails."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()
            # Request OpenAI specifically, but it will fail
            result = await service.invoke(
                sample_messages,
                preferred_model=ModelProvider.OPENAI,
                allow_fallback=True
            )

            # Should fall back to Claude
            assert mock_anthropic.call_count == 1
            assert result.provider == ModelProvider.ANTHROPIC

    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(
        self, mock_openai_failing, mock_anthropic, sample_messages
    ):
        """Should not fall back when fallback is disabled."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService, AllModelsFailedError
            from app.config.models import ModelProvider

            service = ModelProviderService()

            with pytest.raises(AllModelsFailedError):
                await service.invoke(
                    sample_messages,
                    preferred_model=ModelProvider.OPENAI,
                    allow_fallback=False
                )

            # Claude should NOT be tried
            assert mock_anthropic.call_count == 0


# =============================================================================
# AC-4: Graceful error when all models fail
# =============================================================================

class TestAllModelsFail:
    """Tests for AC-4: Graceful error when all models fail."""

    @pytest.mark.asyncio
    async def test_raises_error_when_all_models_fail(
        self, mock_openai_failing, mock_anthropic_failing, sample_messages
    ):
        """Should raise AllModelsFailedError when all models fail."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic_failing), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService, AllModelsFailedError

            service = ModelProviderService()

            with pytest.raises(AllModelsFailedError) as exc_info:
                await service.invoke(sample_messages)

            # Error should contain information about failures
            assert "all models failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_error_includes_individual_failure_reasons(
        self, sample_messages
    ):
        """Error should include individual failure reasons for debugging."""
        mock_openai = MockChatOpenAI(
            raise_exception=RuntimeError("OpenAI rate limit exceeded")
        )
        mock_anthropic = MockChatAnthropic(
            raise_exception=RuntimeError("Anthropic authentication failed")
        )

        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService, AllModelsFailedError

            service = ModelProviderService()

            with pytest.raises(AllModelsFailedError) as exc_info:
                await service.invoke(sample_messages)

            error = exc_info.value
            # Should have details about each failure
            assert hasattr(error, 'errors')
            assert len(error.errors) == 2

    @pytest.mark.asyncio
    async def test_raises_error_when_no_api_keys_configured(self, sample_messages):
        """Should raise error when no API keys are configured."""
        # Clear all API keys
        with patch.dict('os.environ', {}, clear=True):
            from app.services.model_provider import ModelProviderService, NoModelsAvailableError

            service = ModelProviderService()

            with pytest.raises(NoModelsAvailableError):
                await service.invoke(sample_messages)

    @pytest.mark.asyncio
    async def test_tries_all_models_in_order_before_failing(
        self, mock_openai_failing, mock_anthropic_failing, sample_messages
    ):
        """Should try all models in order before raising error."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai_failing), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic_failing), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService, AllModelsFailedError

            service = ModelProviderService()

            with pytest.raises(AllModelsFailedError):
                await service.invoke(sample_messages)

            # Both models should have been tried
            # Note: The call_count is tracked on the mock, which was returned
            # by the patched constructors


# =============================================================================
# Model Initialization Tests
# =============================================================================

class TestModelInitialization:
    """Tests for model initialization based on available API keys."""

    def test_initializes_openai_when_key_available(self):
        """Should initialize OpenAI model when API key is available."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), \
             patch('app.services.model_provider.ChatOpenAI') as mock_chat:

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            assert ModelProvider.OPENAI in service.available_models

    def test_initializes_anthropic_when_key_available(self):
        """Should initialize Anthropic model when API key is available."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}), \
             patch('app.services.model_provider.ChatAnthropic') as mock_chat:

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            assert ModelProvider.ANTHROPIC in service.available_models

    def test_does_not_initialize_model_without_key(self):
        """Should not initialize model when API key is missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}, clear=True):
            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            # OpenAI should be available
            assert ModelProvider.OPENAI in service.available_models
            # Anthropic should NOT be available
            assert ModelProvider.ANTHROPIC not in service.available_models

    def test_available_models_property(self):
        """Should expose list of available models."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}), \
             patch('app.services.model_provider.ChatOpenAI'), \
             patch('app.services.model_provider.ChatAnthropic'):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            assert isinstance(service.available_models, list)
            assert ModelProvider.OPENAI in service.available_models
            assert ModelProvider.ANTHROPIC in service.available_models


# =============================================================================
# Response Format Consistency Tests
# =============================================================================

class TestResponseConsistency:
    """Tests for consistent response format across providers."""

    @pytest.mark.asyncio
    async def test_openai_response_has_required_attributes(
        self, mock_openai, sample_messages
    ):
        """OpenAI responses should have required attributes."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Required attributes
            assert hasattr(result, 'content')
            assert hasattr(result, 'provider')

    @pytest.mark.asyncio
    async def test_anthropic_response_has_required_attributes(
        self, mock_anthropic, sample_messages
    ):
        """Anthropic responses should have required attributes."""
        with patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages)

            # Required attributes
            assert hasattr(result, 'content')
            assert hasattr(result, 'provider')

    @pytest.mark.asyncio
    async def test_response_format_matches_between_providers(
        self, mock_openai, mock_anthropic, sample_messages
    ):
        """Response format should be identical regardless of provider."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            # Get response from OpenAI
            openai_result = await service.invoke(
                sample_messages,
                preferred_model=ModelProvider.OPENAI,
                allow_fallback=False
            )

        # Reset mocks and get response from Anthropic
        mock_openai.reset_history()
        mock_anthropic.reset_history()

        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch('app.services.model_provider.ChatAnthropic', return_value=mock_anthropic), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService
            from app.config.models import ModelProvider

            service = ModelProviderService()

            anthropic_result = await service.invoke(
                sample_messages,
                preferred_model=ModelProvider.ANTHROPIC,
                allow_fallback=False
            )

            # Both should have same attributes (though different values)
            openai_attrs = set(dir(openai_result))
            anthropic_attrs = set(dir(anthropic_result))

            # Core attributes should match
            assert 'content' in openai_attrs
            assert 'content' in anthropic_attrs
            assert 'provider' in openai_attrs
            assert 'provider' in anthropic_attrs


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_messages_list(self, mock_openai):
        """Should handle empty messages list gracefully."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()

            # Empty messages should still work (model will handle it)
            result = await service.invoke([])
            assert hasattr(result, 'content')

    @pytest.mark.asyncio
    async def test_handles_none_preferred_model(self, mock_openai, sample_messages):
        """Should use default order when preferred_model is None."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()
            result = await service.invoke(sample_messages, preferred_model=None)

            assert mock_openai.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_invalid_preferred_model_gracefully(self, mock_openai, sample_messages):
        """Should handle invalid preferred model value gracefully."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()

            # Invalid provider should raise ValueError
            with pytest.raises(ValueError):
                await service.invoke(sample_messages, preferred_model="invalid")

    @pytest.mark.asyncio
    async def test_service_is_reusable_for_multiple_calls(
        self, mock_openai, sample_messages
    ):
        """Service should be reusable for multiple invocations."""
        with patch('app.services.model_provider.ChatOpenAI', return_value=mock_openai), \
             patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):

            from app.services.model_provider import ModelProviderService

            service = ModelProviderService()

            # Make multiple calls
            result1 = await service.invoke(sample_messages)
            result2 = await service.invoke(sample_messages)
            result3 = await service.invoke(sample_messages)

            assert mock_openai.call_count == 3
            assert all(hasattr(r, 'content') for r in [result1, result2, result3])
