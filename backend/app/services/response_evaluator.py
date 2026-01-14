"""
Response Evaluator Service - PRD-010

Evaluates AI responses for confidence scoring and hallucination detection.
Uses source document relevance scores and content coverage to determine
how well-grounded a response is.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

from app.models.response import ConfidenceLevel


@dataclass
class EvaluationResult:
    """
    Result of evaluating an AI response against source documents.

    Attributes:
        confidence_score: Float between 0 and 1 indicating overall confidence
        confidence_level: Categorical level (HIGH, MEDIUM, LOW)
        hallucination_flags: List of potential hallucinations detected
        needs_review: Flag indicating if human review is recommended
        source_coverage: Percentage of response content grounded in sources
    """
    confidence_score: float
    confidence_level: ConfidenceLevel
    hallucination_flags: List[str] = field(default_factory=list)
    needs_review: bool = False
    source_coverage: float = 0.0


class ResponseEvaluator:
    """
    Evaluates AI responses for confidence and hallucination detection.

    The evaluator analyzes:
    1. Source relevance scores - How relevant were the retrieved sources
    2. Content coverage - What percentage of response claims are in sources
    3. Hallucination indicators - Numbers, dates, strong claims not in sources

    Confidence is calculated as:
    - 60% weight on average source relevance scores
    - 40% weight on content coverage
    - Reduced by 30% if hallucinations are detected
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    LOW_CONFIDENCE_THRESHOLD = 0.5

    # Stopwords to ignore in coverage calculation
    STOPWORDS: Set[str] = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "and", "or", "but", "if", "then", "else", "when", "where",
        "how", "what", "which", "who", "this", "that", "these", "those",
        "it", "its", "as", "so", "than", "such", "no", "not", "only",
        "own", "same", "can", "into", "some", "other", "all", "any",
        "each", "few", "more", "most", "very", "just", "also", "now",
        "about", "up", "out", "over", "after", "before", "between",
        "under", "again", "further", "once", "here", "there", "why",
        "because", "through", "during", "while", "above", "below"
    }

    # Patterns for detecting strong/definitive claims
    DEFINITIVE_PATTERNS: List[str] = [
        r"\balways\b",
        r"\bnever\b",
        r"\bguaranteed\b",
        r"\b100%\b",
        r"\bdefinitely\b",
        r"\bcertainly\b",
        r"\babsolutely\b",
        r"\bperfect\b",
    ]

    def __init__(self):
        """Initialize the ResponseEvaluator."""
        pass

    def evaluate(self, response: Optional[str], sources: Optional[List[dict]]) -> EvaluationResult:
        """
        Evaluate an AI response against source documents.

        Args:
            response: The AI-generated response text
            sources: List of source documents with 'content' and 'score' fields

        Returns:
            EvaluationResult with confidence metrics and hallucination flags
        """
        # Handle edge cases
        if not response or not sources:
            return EvaluationResult(
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.LOW,
                needs_review=True,
                source_coverage=0.0
            )

        # Calculate confidence from source relevance scores
        source_scores = [s.get("score", 0.0) for s in sources if isinstance(s, dict)]
        avg_source_score = sum(source_scores) / len(source_scores) if source_scores else 0.0

        # Calculate source coverage - how much of response is grounded
        coverage = self._calculate_coverage(response, sources)

        # Combined confidence: 60% source scores, 40% coverage
        confidence = (avg_source_score * 0.6) + (coverage * 0.4)

        # Detect potential hallucinations
        hallucinations = self._detect_hallucinations(response, sources)

        # Adjust confidence if hallucinations detected
        if hallucinations:
            confidence *= 0.7  # Reduce confidence by 30%

        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))

        # Determine confidence level
        level = self._determine_confidence_level(confidence)

        # Determine if review is needed
        needs_review = (
            level == ConfidenceLevel.LOW
            or len(hallucinations) > 0
        )

        return EvaluationResult(
            confidence_score=round(confidence, 3),
            confidence_level=level,
            hallucination_flags=hallucinations,
            needs_review=needs_review,
            source_coverage=round(coverage, 3)
        )

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Determine the categorical confidence level from a score.

        Args:
            confidence: Float confidence score between 0 and 1

        Returns:
            ConfidenceLevel enum value
        """
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence >= self.LOW_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _calculate_coverage(self, response: str, sources: List[dict]) -> float:
        """
        Calculate what percentage of response content is grounded in sources.

        Uses word overlap approach, filtering out stopwords to focus on
        meaningful content words.

        Args:
            response: The AI-generated response text
            sources: List of source documents

        Returns:
            Float between 0 and 1 representing coverage percentage
        """
        response_lower = response.lower()
        source_content = " ".join(
            s.get("content", "") for s in sources if isinstance(s, dict)
        ).lower()

        # Extract meaningful words (filter stopwords)
        response_words = self._extract_meaningful_words(response_lower)
        source_words = self._extract_meaningful_words(source_content)

        if not response_words:
            return 0.0

        # Calculate overlap
        overlap = response_words & source_words
        return len(overlap) / len(response_words)

    def _extract_meaningful_words(self, text: str) -> Set[str]:
        """
        Extract meaningful words from text, filtering stopwords.

        Args:
            text: Input text to process

        Returns:
            Set of meaningful words
        """
        # Split on whitespace and non-alphanumeric characters
        words = set(re.findall(r'\b[a-z]+\b', text.lower()))
        # Filter stopwords and very short words
        return {w for w in words if w not in self.STOPWORDS and len(w) > 2}

    def _detect_hallucinations(self, response: str, sources: List[dict]) -> List[str]:
        """
        Detect potential hallucinations - claims not grounded in sources.

        Checks for:
        1. Numeric claims (prices, percentages) not in sources
        2. Date/time claims not in sources
        3. Strong definitive claims not in sources

        Args:
            response: The AI-generated response text
            sources: List of source documents

        Returns:
            List of hallucination flag messages
        """
        hallucinations = []
        response_lower = response.lower()
        source_content = " ".join(
            s.get("content", "") for s in sources if isinstance(s, dict)
        ).lower()

        # Check for ungrounded numeric claims
        hallucinations.extend(
            self._check_numeric_claims(response_lower, source_content)
        )

        # Check for ungrounded date/time claims
        hallucinations.extend(
            self._check_date_claims(response_lower, source_content)
        )

        # Check for strong definitive claims
        hallucinations.extend(
            self._check_definitive_claims(response_lower, source_content)
        )

        return hallucinations

    def _check_numeric_claims(self, response: str, source_content: str) -> List[str]:
        """
        Check for numeric claims in response not present in sources.

        Args:
            response: Lowercase response text
            source_content: Lowercase combined source content

        Returns:
            List of hallucination flags for ungrounded numbers
        """
        flags = []

        # Pattern for prices ($XXX), percentages (XX%), and plain numbers
        numeric_patterns = [
            (r'\$[\d,]+(?:\.\d{2})?', "price"),
            (r'\d+(?:\.\d+)?%', "percentage"),
            (r'\b\d{2,}\b', "number"),  # Numbers with 2+ digits
        ]

        for pattern, claim_type in numeric_patterns:
            response_matches = set(re.findall(pattern, response))
            source_matches = set(re.findall(pattern, source_content))

            ungrounded = response_matches - source_matches
            for num in ungrounded:
                flags.append(f"Ungrounded {claim_type}: {num}")

        return flags

    def _check_date_claims(self, response: str, source_content: str) -> List[str]:
        """
        Check for date/time claims in response not present in sources.

        Args:
            response: Lowercase response text
            source_content: Lowercase combined source content

        Returns:
            List of hallucination flags for ungrounded dates
        """
        flags = []

        # Patterns for dates
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years like 2020, 1995
            r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b',  # MM/DD or MM/DD/YYYY
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b',  # Month Day
            r'\b\d{1,2}(?:st|nd|rd|th)\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)\b',  # Day of Month
        ]

        for pattern in date_patterns:
            response_matches = set(re.findall(pattern, response))
            source_matches = set(re.findall(pattern, source_content))

            ungrounded = response_matches - source_matches
            for date in ungrounded:
                if len(str(date)) > 3:  # Avoid very short matches
                    flags.append(f"Ungrounded date/time: {date}")

        return flags

    def _check_definitive_claims(self, response: str, source_content: str) -> List[str]:
        """
        Check for strong definitive claims not present in sources.

        Args:
            response: Lowercase response text
            source_content: Lowercase combined source content

        Returns:
            List of hallucination flags for ungrounded strong claims
        """
        flags = []

        for pattern in self.DEFINITIVE_PATTERNS:
            if re.search(pattern, response) and not re.search(pattern, source_content):
                # Extract the matched word for the flag message
                match = re.search(pattern, response)
                if match:
                    word = match.group().strip()
                    flags.append(f"Strong claim not in sources: {word}")

        return flags


# Singleton instance for convenient imports
response_evaluator = ResponseEvaluator()
