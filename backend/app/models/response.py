"""
Response Model with Confidence Scoring - PRD-010

Provides data classes for evaluated AI responses with confidence metrics
and hallucination detection.
"""

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.services.response_evaluator import ResponseEvaluator


class ConfidenceLevel(Enum):
    """Confidence level categories for AI responses."""
    HIGH = "high"      # > 0.8 - Strong source support
    MEDIUM = "medium"  # 0.5 - 0.8 - Moderate source support
    LOW = "low"        # < 0.5 - Weak or no source support


@dataclass
class EvaluatedResponse:
    """
    Represents an AI response that has been evaluated for confidence
    and potential hallucinations.

    Attributes:
        response: The original AI-generated response text
        confidence_score: Float between 0 and 1 indicating confidence level
        confidence_level: Categorical confidence level (HIGH, MEDIUM, LOW)
        sources_used: List of source identifiers used for the response
        hallucination_flags: List of detected potential hallucinations
        needs_review: Flag indicating if human review is recommended
    """
    response: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    sources_used: List[str]
    hallucination_flags: List[str] = field(default_factory=list)
    needs_review: bool = False

    @classmethod
    def from_raw(
        cls,
        response: str,
        sources: List[dict],
        evaluator: "ResponseEvaluator"
    ) -> "EvaluatedResponse":
        """
        Factory method to create an EvaluatedResponse from raw response and sources.

        Args:
            response: The AI-generated response text
            sources: List of source documents with 'content', 'score', and 'source' fields
            evaluator: ResponseEvaluator instance to perform evaluation

        Returns:
            EvaluatedResponse with confidence metrics and hallucination detection
        """
        result = evaluator.evaluate(response, sources)

        return cls(
            response=response,
            confidence_score=result.confidence_score,
            confidence_level=result.confidence_level,
            sources_used=[s.get("source", "") for s in sources if isinstance(s, dict)],
            hallucination_flags=result.hallucination_flags,
            needs_review=result.needs_review
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "response": self.response,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "sources_used": self.sources_used,
            "hallucination_flags": self.hallucination_flags,
            "needs_review": self.needs_review
        }

    @property
    def is_reliable(self) -> bool:
        """Check if the response is considered reliable (high confidence, no hallucinations)."""
        return (
            self.confidence_level == ConfidenceLevel.HIGH
            and len(self.hallucination_flags) == 0
            and not self.needs_review
        )
