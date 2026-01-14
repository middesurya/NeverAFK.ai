"""
PRD-007: Multi-Model Support with Fallback Chains

Provides a unified interface for invoking LLM models with automatic fallback.
Supports OpenAI and Anthropic (Claude) with graceful degradation.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.config.models import (
    ModelProvider,
    MODEL_CONFIG,
    DEFAULT_MODEL_ORDER,
    API_KEY_ENV_VARS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================

class ModelProviderError(Exception):
    """Base exception for model provider errors."""
    pass


class NoModelsAvailableError(ModelProviderError):
    """Raised when no models are available (no API keys configured)."""

    def __init__(self, message: str = "No models available - no API keys configured"):
        self.message = message
        super().__init__(self.message)


class AllModelsFailedError(ModelProviderError):
    """Raised when all models in the fallback chain have failed."""

    def __init__(self, errors: Dict[ModelProvider, Exception]):
        self.errors = errors
        error_details = ", ".join(
            f"{provider.value}: {str(error)}"
            for provider, error in errors.items()
        )
        self.message = f"All models failed to generate response: {error_details}"
        super().__init__(self.message)


# =============================================================================
# Response Wrapper for Consistent Format
# =============================================================================

@dataclass
class ModelResponse:
    """
    Unified response format for all model providers.

    Ensures consistent interface regardless of which model was used.
    """
    content: str
    provider: ModelProvider
    raw_response: Any = None

    def __post_init__(self):
        """Validate response data."""
        if not isinstance(self.content, str):
            self.content = str(self.content)


# =============================================================================
# Model Provider Service
# =============================================================================

class ModelProviderService:
    """
    Service for invoking LLM models with automatic fallback support.

    Features:
    - Automatic model initialization based on available API keys
    - Primary model preference with fallback chain
    - Explicit model selection support
    - Consistent response format across providers
    - Graceful error handling

    Example:
        service = ModelProviderService()
        response = await service.invoke(messages)
        print(response.content)
        print(f"Used: {response.provider.value}")
    """

    def __init__(self):
        """Initialize the service and available models."""
        self._models: Dict[ModelProvider, Any] = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        """
        Initialize available models based on API keys in environment.

        Only initializes models for which API keys are configured.
        """
        for provider in ModelProvider:
            api_key_var = API_KEY_ENV_VARS.get(provider)
            api_key = os.environ.get(api_key_var) if api_key_var else None

            if api_key:
                try:
                    model = self._create_model(provider, api_key)
                    self._models[provider] = model
                    logger.info(f"Initialized {provider.value} model")
                except Exception as e:
                    logger.warning(f"Failed to initialize {provider.value}: {e}")
            else:
                logger.debug(f"No API key for {provider.value}, skipping")

    def _create_model(self, provider: ModelProvider, api_key: str) -> Any:
        """
        Create a model instance for the given provider.

        Args:
            provider: The model provider enum value
            api_key: The API key for the provider

        Returns:
            Configured LangChain chat model instance
        """
        config = MODEL_CONFIG.get(provider, {})

        if provider == ModelProvider.OPENAI:
            return ChatOpenAI(
                model=config.get("model", "gpt-4o-mini"),
                temperature=config.get("temperature", 0.3),
                max_tokens=config.get("max_tokens", 4096),
                api_key=api_key,
            )
        elif provider == ModelProvider.ANTHROPIC:
            return ChatAnthropic(
                model=config.get("model", "claude-3-haiku-20240307"),
                temperature=config.get("temperature", 0.3),
                max_tokens=config.get("max_tokens", 4096),
                api_key=api_key,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @property
    def available_models(self) -> List[ModelProvider]:
        """
        Get list of currently available model providers.

        Returns:
            List of ModelProvider enum values for available models
        """
        return list(self._models.keys())

    def _get_model_order(
        self,
        preferred_model: Optional[ModelProvider] = None
    ) -> List[ModelProvider]:
        """
        Determine the order of models to try.

        Args:
            preferred_model: Optional preferred model to try first

        Returns:
            Ordered list of ModelProvider values to attempt
        """
        if preferred_model is not None:
            # Validate preferred_model is a valid ModelProvider
            if not isinstance(preferred_model, ModelProvider):
                raise ValueError(
                    f"preferred_model must be a ModelProvider enum, got: {type(preferred_model)}"
                )

            # Put preferred model first, then others in default order
            order = [preferred_model]
            for provider in DEFAULT_MODEL_ORDER:
                if provider != preferred_model and provider in self._models:
                    order.append(provider)
            return order

        # Use default order, filtered to available models
        return [p for p in DEFAULT_MODEL_ORDER if p in self._models]

    async def _try_model(
        self,
        provider: ModelProvider,
        messages: List[Any]
    ) -> Optional[ModelResponse]:
        """
        Attempt to invoke a specific model.

        Args:
            provider: The model provider to try
            messages: The messages to send to the model

        Returns:
            ModelResponse if successful, None if failed

        Raises:
            Exception: Re-raises any exception from the model
        """
        if provider not in self._models:
            logger.warning(f"Model {provider.value} not available")
            return None

        model = self._models[provider]

        logger.debug(f"Trying {provider.value} model")
        response = await model.ainvoke(messages)

        # Extract content from response
        content = response.content if hasattr(response, 'content') else str(response)

        return ModelResponse(
            content=content,
            provider=provider,
            raw_response=response
        )

    async def invoke(
        self,
        messages: List[Any],
        preferred_model: Optional[ModelProvider] = None,
        allow_fallback: bool = True
    ) -> ModelResponse:
        """
        Invoke an LLM model with automatic fallback support.

        Args:
            messages: List of messages to send to the model
            preferred_model: Optional specific model to use first
            allow_fallback: Whether to try other models on failure (default: True)

        Returns:
            ModelResponse with content, provider used, and raw response

        Raises:
            NoModelsAvailableError: When no models are configured
            AllModelsFailedError: When all models fail
            ValueError: When preferred_model is invalid
        """
        # Check if any models are available
        if not self._models:
            raise NoModelsAvailableError()

        # Validate preferred_model if provided
        if preferred_model is not None and not isinstance(preferred_model, ModelProvider):
            raise ValueError(
                f"preferred_model must be a ModelProvider enum, got: {type(preferred_model)}"
            )

        # Determine model order
        model_order = self._get_model_order(preferred_model)

        # If fallback is disabled, only try the first (preferred) model
        if not allow_fallback:
            model_order = model_order[:1]

        # Track errors for reporting
        errors: Dict[ModelProvider, Exception] = {}

        # Try each model in order
        for provider in model_order:
            if provider not in self._models:
                continue

            try:
                result = await self._try_model(provider, messages)
                if result is not None:
                    logger.info(f"Successfully used {provider.value} model")
                    return result
            except Exception as e:
                logger.warning(f"{provider.value} failed: {e}")
                errors[provider] = e

                # If fallback is disabled, don't continue
                if not allow_fallback:
                    break

        # All models failed
        raise AllModelsFailedError(errors)
