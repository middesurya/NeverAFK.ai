"""
PRD-009: Prompt Injection Detection Module

This module provides prompt injection detection capabilities to protect LLM
interactions from malicious input attacks.

Key Features:
- Detects instruction override attempts
- Detects role-playing/jailbreak attacks
- Normalizes unicode obfuscation tricks
- Classifies threat levels
- Logs detection attempts for security monitoring
"""

import re
import logging
from typing import List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Classification of threat severity for detected injections."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class InjectionCheckResult:
    """Result of a prompt injection check.

    Attributes:
        is_injection: Whether the input was detected as an injection attempt
        threat_level: Severity classification of the threat
        matched_pattern: The pattern that triggered detection (empty if clean)
        sanitized_input: The input if clean, empty string if injection detected
    """
    is_injection: bool
    threat_level: ThreatLevel
    matched_pattern: str = ""
    sanitized_input: str = ""


class PromptGuard:
    """
    Prompt injection detection and prevention system.

    This class provides pattern-based detection of common prompt injection
    techniques including instruction overrides, role-playing attacks,
    and jailbreak attempts.

    Example:
        guard = PromptGuard()
        result = guard.check_input("ignore previous instructions")
        if result.is_injection:
            # Handle the injection attempt
            pass
    """

    # Patterns for instruction override attempts
    INSTRUCTION_OVERRIDE_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"disregard\s+(all\s+)?(previous|prior|above)",
        r"forget\s+(everything|all|what)\s+(you|i)\s+(said|told|were)",
        r"new\s+instructions?:?\s*",
        r"override\s+(system|previous)",
    ]

    # Patterns for role-playing/persona manipulation attempts
    ROLE_PLAYING_PATTERNS = [
        r"you\s+are\s+now\s+",
        r"pretend\s+(to\s+be|you\s+are)",
        r"act\s+as\s+(if\s+you\s+are|a)",
        r"imagine\s+you\s+are",
        r"from\s+now\s+on\s+you\s+are",
        r"i\s+want\s+you\s+to\s+act\s+as",
    ]

    # Patterns for known jailbreak techniques
    JAILBREAK_PATTERNS = [
        r"DAN\s+mode",
        r"developer\s+mode",
        r"\bjailbreak\b",
        r"bypass\s+(your\s+)?(safety|restrictions|filters)",
    ]

    # Unicode characters commonly used for obfuscation
    UNICODE_OBFUSCATION_CHARS = {
        '\u200b': '',  # zero-width space
        '\u200c': '',  # zero-width non-joiner
        '\u200d': '',  # zero-width joiner
        '\ufeff': '',  # byte order mark
        '\u00ad': '',  # soft hyphen
        '\u2060': '',  # word joiner
        '\u180e': '',  # mongolian vowel separator
    }

    def __init__(self):
        """Initialize the PromptGuard with compiled regex patterns."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns for efficient matching."""
        self.instruction_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.INSTRUCTION_OVERRIDE_PATTERNS
        ]
        self.role_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.ROLE_PLAYING_PATTERNS
        ]
        self.jailbreak_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS
        ]

    def check_input(self, text: str) -> InjectionCheckResult:
        """
        Check input text for prompt injection attempts.

        This method analyzes the input text for various injection patterns
        and returns a result indicating whether an injection was detected,
        the threat level, and other relevant information.

        Args:
            text: The user input text to check

        Returns:
            InjectionCheckResult with detection results
        """
        # Handle empty or whitespace-only input
        if not text or not text.strip():
            return InjectionCheckResult(
                is_injection=False,
                threat_level=ThreatLevel.NONE,
                sanitized_input=text.strip() if text else ""
            )

        # Normalize text to handle obfuscation attempts
        normalized = self._normalize(text)

        # Check high threat patterns first (jailbreak attempts)
        for pattern in self.jailbreak_patterns:
            match = pattern.search(normalized)
            if match:
                logger.warning(
                    f"High threat injection detected (jailbreak): {match.group()}"
                )
                return InjectionCheckResult(
                    is_injection=True,
                    threat_level=ThreatLevel.HIGH,
                    matched_pattern=match.group(),
                    sanitized_input=""
                )

        # Check instruction override patterns (high threat)
        for pattern in self.instruction_patterns:
            match = pattern.search(normalized)
            if match:
                logger.warning(
                    f"High threat injection detected (instruction override): {match.group()}"
                )
                return InjectionCheckResult(
                    is_injection=True,
                    threat_level=ThreatLevel.HIGH,
                    matched_pattern=match.group(),
                    sanitized_input=""
                )

        # Check role-playing patterns (medium threat)
        for pattern in self.role_patterns:
            match = pattern.search(normalized)
            if match:
                logger.warning(
                    f"Medium threat injection detected (role-playing): {match.group()}"
                )
                return InjectionCheckResult(
                    is_injection=True,
                    threat_level=ThreatLevel.MEDIUM,
                    matched_pattern=match.group(),
                    sanitized_input=""
                )

        # Input is clean
        return InjectionCheckResult(
            is_injection=False,
            threat_level=ThreatLevel.NONE,
            sanitized_input=text
        )

    def _normalize(self, text: str) -> str:
        """
        Normalize text by removing obfuscation characters.

        This method removes various unicode characters that are commonly
        used to bypass text-based detection systems.

        Args:
            text: The text to normalize

        Returns:
            Normalized text with obfuscation characters removed
        """
        result = text

        # Remove unicode obfuscation characters
        for old, new in self.UNICODE_OBFUSCATION_CHARS.items():
            result = result.replace(old, new)

        return result.strip()


# Singleton instance for convenience
prompt_guard = PromptGuard()
