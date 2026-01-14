"""
Tests for Response Evaluation - PRD-010
Tests confidence scoring and hallucination detection for AI responses.

TDD RED PHASE - These tests are written first, before implementation.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Ensure mocks are set up before importing our modules
if 'app.models.response' not in sys.modules:
    pass  # Will be imported after we create the module


class TestHighConfidence:
    """AC-1: AI response with strong source matches -> high confidence score (>0.8)"""

    def test_high_confidence_with_strong_source_matches(self):
        """Strong source matches should result in confidence > 0.8"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Python is a programming language created by Guido van Rossum"
        sources = [
            {"content": "Python is a popular programming language", "score": 0.95},
            {"content": "Python was created by Guido van Rossum in 1991", "score": 0.92}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score > 0.8
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_high_confidence_with_perfect_content_match(self):
        """When response content exactly matches sources, confidence should be high"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Machine learning is a subset of artificial intelligence"
        sources = [
            {"content": "Machine learning is a subset of artificial intelligence", "score": 0.98},
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score > 0.8
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_high_confidence_multiple_relevant_sources(self):
        """Multiple highly relevant sources should boost confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "React is a JavaScript library for building user interfaces"
        sources = [
            {"content": "React is a JavaScript library", "score": 0.95},
            {"content": "React is used for building user interfaces", "score": 0.93},
            {"content": "React was developed by Facebook", "score": 0.90}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score > 0.8
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_high_confidence_no_review_needed(self):
        """High confidence responses should not need review"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Django is a Python web framework"
        sources = [
            {"content": "Django is a high-level Python web framework", "score": 0.95},
            {"content": "Django encourages rapid development", "score": 0.90}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score > 0.8
        assert result.needs_review is False

    def test_high_confidence_with_numerical_data_in_sources(self):
        """Response with numbers that exist in sources should have high confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "The course costs $199 and includes 20 lessons"
        sources = [
            {"content": "The course costs $199 for full access", "score": 0.92},
            {"content": "This course includes 20 comprehensive lessons", "score": 0.90}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score > 0.8
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert len(result.hallucination_flags) == 0


class TestLowConfidence:
    """AC-2: AI response with weak source matches -> low confidence score (<0.5)"""

    def test_low_confidence_with_weak_source_matches(self):
        """Weak source matches should result in confidence < 0.5"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "The weather is nice today for a picnic"
        sources = [
            {"content": "Python is a programming language", "score": 0.2},
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_low_confidence_with_unrelated_sources(self):
        """Completely unrelated sources should result in low confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Quantum computing uses qubits instead of classical bits"
        sources = [
            {"content": "How to make a chocolate cake recipe", "score": 0.15},
            {"content": "Best hiking trails in Colorado", "score": 0.10}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_low_confidence_with_empty_response(self):
        """Empty response should have low confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = ""
        sources = [
            {"content": "Python is great", "score": 0.9},
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_low_confidence_with_no_sources(self):
        """No sources should result in low confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Python is a programming language"
        sources = []

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_low_confidence_with_low_score_sources(self):
        """Sources with very low scores should result in low confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Python supports object-oriented programming"
        sources = [
            {"content": "Python supports OOP", "score": 0.25},
            {"content": "OOP is a paradigm", "score": 0.20}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_low_confidence_triggers_review(self):
        """Low confidence should trigger needs_review flag"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Random unrelated information"
        sources = [
            {"content": "Python programming basics", "score": 0.1}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.confidence_score < 0.5
        assert result.needs_review is True


class TestMediumConfidence:
    """Tests for medium confidence range (0.5 - 0.8)"""

    def test_medium_confidence_with_moderate_matches(self):
        """Moderate source matches should result in medium confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Python can be used for web development"
        sources = [
            {"content": "Python is versatile and can build websites", "score": 0.65},
            {"content": "Web development frameworks exist for Python", "score": 0.60}
        ]

        result = evaluator.evaluate(response, sources)

        assert 0.5 <= result.confidence_score <= 0.8
        assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_medium_confidence_partial_content_overlap(self):
        """Partial content overlap should result in medium confidence"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()
        response = "Flask is a lightweight Python framework for web applications"
        sources = [
            {"content": "Flask is a Python micro-framework", "score": 0.70},
        ]

        result = evaluator.evaluate(response, sources)

        assert 0.5 <= result.confidence_score <= 0.8
        assert result.confidence_level == ConfidenceLevel.MEDIUM


class TestHallucinationDetection:
    """AC-3: Response with claims not in sources -> flags potential hallucination"""

    def test_detects_ungrounded_numbers(self):
        """Numbers not present in sources should be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "The course costs $499 and has 50% completion rate"
        sources = [
            {"content": "The course is about Python programming", "score": 0.8}
        ]

        result = evaluator.evaluate(response, sources)

        assert len(result.hallucination_flags) > 0
        # Check that at least one flag mentions an ungrounded number
        flags_text = " ".join(result.hallucination_flags).lower()
        assert "ungrounded" in flags_text or "number" in flags_text or "$499" in flags_text or "50%" in flags_text

    def test_detects_ungrounded_percentages(self):
        """Percentages not in sources should be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "This technique improves performance by 85%"
        sources = [
            {"content": "This technique improves application performance", "score": 0.85}
        ]

        result = evaluator.evaluate(response, sources)

        assert len(result.hallucination_flags) > 0

    def test_detects_ungrounded_dates(self):
        """Dates not in sources should be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python was released in 2020 and updated in March 15th"
        sources = [
            {"content": "Python is a programming language that continues to evolve", "score": 0.8}
        ]

        result = evaluator.evaluate(response, sources)

        assert len(result.hallucination_flags) > 0

    def test_detects_strong_claims_not_in_sources(self):
        """Strong definitive claims not in sources should be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python is always the best choice and is guaranteed to work"
        sources = [
            {"content": "Python is a popular programming language", "score": 0.85}
        ]

        result = evaluator.evaluate(response, sources)

        assert len(result.hallucination_flags) > 0
        flags_text = " ".join(result.hallucination_flags).lower()
        assert "always" in flags_text or "guaranteed" in flags_text or "strong claim" in flags_text

    def test_no_hallucination_when_claims_grounded(self):
        """When all claims are in sources, no hallucination should be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python is a programming language"
        sources = [
            {"content": "Python is a programming language used worldwide", "score": 0.95}
        ]

        result = evaluator.evaluate(response, sources)

        assert len(result.hallucination_flags) == 0

    def test_hallucination_reduces_confidence(self):
        """Detected hallucinations should reduce confidence score"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()

        # Response without hallucination
        response_clean = "Python is a programming language"
        sources = [
            {"content": "Python is a programming language", "score": 0.90}
        ]
        result_clean = evaluator.evaluate(response_clean, sources)

        # Response with hallucination (same sources, but fabricated claims)
        response_hallucinated = "Python is a programming language that costs $999 and is 100% perfect"
        result_hallucinated = evaluator.evaluate(response_hallucinated, sources)

        # Hallucinated response should have lower confidence
        assert result_hallucinated.confidence_score < result_clean.confidence_score

    def test_multiple_hallucinations_detected(self):
        """Multiple ungrounded claims should all be flagged"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "The course costs $299, takes 2 weeks, guarantees 95% success rate, and is always available"
        sources = [
            {"content": "This is a comprehensive Python course", "score": 0.8}
        ]

        result = evaluator.evaluate(response, sources)

        # Should detect multiple hallucinations
        assert len(result.hallucination_flags) >= 2


class TestNeedsReviewFlag:
    """AC-4: Low confidence response -> includes needs_review flag"""

    def test_low_confidence_triggers_review(self):
        """Low confidence should set needs_review to True"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Random unrelated content about gardening"
        sources = [
            {"content": "Python programming tutorial", "score": 0.1}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.needs_review is True

    def test_hallucination_triggers_review(self):
        """Hallucinations should trigger needs_review even with decent source scores"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python definitely costs $9999 and is guaranteed to solve all problems"
        sources = [
            {"content": "Python is a versatile programming language", "score": 0.85}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.needs_review is True

    def test_high_confidence_no_hallucination_no_review(self):
        """High confidence with no hallucinations should not need review"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python is a programming language"
        sources = [
            {"content": "Python is a popular programming language", "score": 0.95},
            {"content": "Python was created by Guido", "score": 0.90}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.needs_review is False

    def test_empty_sources_triggers_review(self):
        """Empty sources should trigger needs_review"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python is great"
        sources = []

        result = evaluator.evaluate(response, sources)

        assert result.needs_review is True

    def test_empty_response_triggers_review(self):
        """Empty response should trigger needs_review"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = ""
        sources = [{"content": "Python programming", "score": 0.9}]

        result = evaluator.evaluate(response, sources)

        assert result.needs_review is True


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass structure"""

    def test_evaluation_result_has_all_fields(self):
        """EvaluationResult should have all required fields"""
        from app.services.response_evaluator import ResponseEvaluator, EvaluationResult

        evaluator = ResponseEvaluator()
        response = "Test response"
        sources = [{"content": "Test content", "score": 0.7}]

        result = evaluator.evaluate(response, sources)

        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'confidence_level')
        assert hasattr(result, 'hallucination_flags')
        assert hasattr(result, 'needs_review')
        assert hasattr(result, 'source_coverage')

    def test_confidence_score_is_rounded(self):
        """Confidence score should be rounded to 3 decimal places"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python programming"
        sources = [{"content": "Python programming", "score": 0.8}]

        result = evaluator.evaluate(response, sources)

        # Check that the score has at most 3 decimal places
        score_str = str(result.confidence_score)
        if '.' in score_str:
            decimal_places = len(score_str.split('.')[1])
            assert decimal_places <= 3

    def test_confidence_score_in_valid_range(self):
        """Confidence score should be between 0 and 1"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()

        # Test with various inputs
        test_cases = [
            ("Test", [{"content": "Test", "score": 0.5}]),
            ("", []),
            ("Long response " * 100, [{"content": "Test", "score": 1.0}]),
        ]

        for response, sources in test_cases:
            result = evaluator.evaluate(response, sources)
            assert 0.0 <= result.confidence_score <= 1.0


class TestEvaluatedResponse:
    """Tests for EvaluatedResponse model"""

    def test_evaluated_response_from_raw(self):
        """Test EvaluatedResponse.from_raw factory method"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import EvaluatedResponse

        evaluator = ResponseEvaluator()
        response = "Python is a programming language"
        sources = [
            {"content": "Python is a programming language", "score": 0.9, "source": "docs/python.md"},
        ]

        evaluated = EvaluatedResponse.from_raw(response, sources, evaluator)

        assert evaluated.response == response
        assert evaluated.confidence_score > 0
        assert evaluated.sources_used == ["docs/python.md"]

    def test_evaluated_response_confidence_levels(self):
        """Test that confidence levels are properly assigned"""
        from app.models.response import ConfidenceLevel

        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_evaluated_response_defaults(self):
        """Test EvaluatedResponse default values"""
        from app.models.response import EvaluatedResponse, ConfidenceLevel

        evaluated = EvaluatedResponse(
            response="Test",
            confidence_score=0.5,
            confidence_level=ConfidenceLevel.MEDIUM,
            sources_used=[]
        )

        assert evaluated.hallucination_flags == []
        assert evaluated.needs_review is False


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_none_response(self):
        """None response should be handled gracefully"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()

        result = evaluator.evaluate(None, [{"content": "test", "score": 0.9}])

        assert result.confidence_score == 0.0
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.needs_review is True

    def test_none_sources(self):
        """None sources should be handled gracefully"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()

        result = evaluator.evaluate("Test response", None)

        assert result.confidence_score == 0.0
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.needs_review is True

    def test_sources_missing_score(self):
        """Sources without score field should default to 0"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Test response"
        sources = [{"content": "Test content"}]  # No score field

        result = evaluator.evaluate(response, sources)

        # Should not crash and should handle gracefully
        assert result.confidence_score >= 0.0

    def test_sources_missing_content(self):
        """Sources without content field should be handled"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Test response"
        sources = [{"score": 0.9}]  # No content field

        result = evaluator.evaluate(response, sources)

        # Should not crash
        assert result.confidence_score >= 0.0

    def test_very_long_response(self):
        """Very long responses should be handled"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python programming " * 1000
        sources = [{"content": "Python programming basics", "score": 0.8}]

        result = evaluator.evaluate(response, sources)

        assert 0.0 <= result.confidence_score <= 1.0

    def test_special_characters_in_response(self):
        """Special characters should not break evaluation"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Test @#$%^&*() response with unicode: \u00e9\u00e8\u00ea"
        sources = [{"content": "Test response", "score": 0.7}]

        result = evaluator.evaluate(response, sources)

        assert 0.0 <= result.confidence_score <= 1.0

    def test_boundary_confidence_threshold_high(self):
        """Test boundary at high confidence threshold (0.8)"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()

        # This should result in confidence close to but at 0.8
        response = "Test content"
        sources = [{"content": "Test content exact match", "score": 0.80}]

        result = evaluator.evaluate(response, sources)

        # At exactly 0.8 it should be HIGH (>= threshold)
        if result.confidence_score >= 0.8:
            assert result.confidence_level == ConfidenceLevel.HIGH

    def test_boundary_confidence_threshold_low(self):
        """Test boundary at low confidence threshold (0.5)"""
        from app.services.response_evaluator import ResponseEvaluator
        from app.models.response import ConfidenceLevel

        evaluator = ResponseEvaluator()

        # This should result in confidence around 0.5
        response = "Test content"
        sources = [{"content": "Somewhat related test", "score": 0.50}]

        result = evaluator.evaluate(response, sources)

        # At exactly 0.5 it should be MEDIUM (>= threshold)
        if result.confidence_score >= 0.5 and result.confidence_score < 0.8:
            assert result.confidence_level == ConfidenceLevel.MEDIUM


class TestResponseEvaluatorSingleton:
    """Tests for singleton instance"""

    def test_singleton_instance_exists(self):
        """response_evaluator singleton should be available"""
        from app.services.response_evaluator import response_evaluator

        assert response_evaluator is not None

    def test_singleton_is_response_evaluator(self):
        """Singleton should be an instance of ResponseEvaluator"""
        from app.services.response_evaluator import response_evaluator, ResponseEvaluator

        assert isinstance(response_evaluator, ResponseEvaluator)


class TestSourceCoverage:
    """Tests for source coverage calculation"""

    def test_high_coverage_with_matching_content(self):
        """High word overlap should result in high coverage"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Python is used for data science and machine learning"
        sources = [
            {"content": "Python is commonly used for data science and machine learning applications", "score": 0.9}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.source_coverage > 0.5

    def test_low_coverage_with_different_content(self):
        """Low word overlap should result in low coverage"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        response = "Quantum computing uses superposition and entanglement"
        sources = [
            {"content": "Python is a programming language for web development", "score": 0.3}
        ]

        result = evaluator.evaluate(response, sources)

        assert result.source_coverage < 0.5

    def test_stopwords_ignored_in_coverage(self):
        """Common stopwords should not inflate coverage"""
        from app.services.response_evaluator import ResponseEvaluator

        evaluator = ResponseEvaluator()
        # Response with many stopwords
        response = "The is a an of in for on with by from"
        sources = [
            {"content": "Python is a programming language", "score": 0.5}
        ]

        result = evaluator.evaluate(response, sources)

        # Coverage should be low because stopwords are filtered
        assert result.source_coverage < 0.3
