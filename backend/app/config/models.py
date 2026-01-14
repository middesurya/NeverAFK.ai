"""
PRD-007: Multi-Model Support Configuration

Defines model providers, their configurations, and the default fallback order.
"""

from enum import Enum
from typing import Dict, Any, List


class ModelProvider(Enum):
    """Enumeration of supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Model-specific configuration settings
MODEL_CONFIG: Dict[ModelProvider, Dict[str, Any]] = {
    ModelProvider.OPENAI: {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    ModelProvider.ANTHROPIC: {
        "model": "claude-3-haiku-20240307",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
}

# Default order for fallback chain
# Primary model is first, fallbacks follow in order
DEFAULT_MODEL_ORDER: List[ModelProvider] = [
    ModelProvider.OPENAI,
    ModelProvider.ANTHROPIC
]

# Environment variable names for API keys
API_KEY_ENV_VARS: Dict[ModelProvider, str] = {
    ModelProvider.OPENAI: "OPENAI_API_KEY",
    ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
}
