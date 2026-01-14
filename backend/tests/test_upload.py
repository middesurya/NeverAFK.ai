"""
PRD-004: Integration Tests for API Endpoints - Upload Tests

Tests for POST /upload/content endpoint:
- AC-3: POST /upload/content returns 200 with confirmation

These tests verify file upload handling including validation,
content type processing, and proper responses.
"""

import pytest
import io
from unittest.mock import patch, MagicMock, AsyncMock

from tests.mocks.supabase_mock import MockDatabase


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_text_file():
    """Create a sample text file for upload testing."""
    content = b"This is sample text content for testing the upload endpoint."
    return ("test_document.txt", io.BytesIO(content), "text/plain")


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file (simulated) for upload testing."""
    # PDF header bytes (simplified)
    content = b"%PDF-1.4 sample pdf content for testing"
    return ("test_document.pdf", io.BytesIO(content), "application/pdf")


@pytest.fixture
def sample_video_file():
    """Create a sample video file (simulated) for upload testing."""
    content = b"fake video content for testing"
    return ("test_video.mp4", io.BytesIO(content), "video/mp4")


@pytest.fixture
def mock_ingestion_result():
    """Mock result from content ingestion service."""
    return {
        "status": "success",
        "chunks_created": 5,
        "document_count": 1
    }


# =============================================================================
# AC-3: POST /upload/content returns 200 with confirmation
# =============================================================================

class TestUploadSuccess:
    """Tests for successful file upload - AC-3."""

    def test_upload_text_returns_200(self, client, sample_text_file, mock_ingestion_result):
        """Upload text file should return 200."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            assert response.status_code == 200

    def test_upload_returns_status_success(self, client, sample_text_file, mock_ingestion_result):
        """Upload should return status success."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()
            assert "status" in data
            assert data["status"] == "success"

    def test_upload_returns_filename(self, client, sample_text_file, mock_ingestion_result):
        """Upload should return the uploaded filename."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()
            assert "filename" in data
            assert data["filename"] == "test_document.txt"

    def test_upload_returns_creator_id(self, client, sample_text_file, mock_ingestion_result):
        """Upload should return the creator_id."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()
            assert "creator_id" in data
            assert data["creator_id"] == "test-creator-123"

    def test_upload_returns_content_type(self, client, sample_text_file, mock_ingestion_result):
        """Upload should return the content_type."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()
            assert "content_type" in data
            assert data["content_type"] == "text"

    def test_upload_pdf_returns_200(self, client, sample_pdf_file, mock_ingestion_result):
        """Upload PDF file should return 200."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_pdf_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "pdf"
                }
            )

            assert response.status_code == 200

    def test_upload_video_returns_200(self, client, sample_video_file, mock_ingestion_result):
        """Upload video file should return 200."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_video_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "video"
                }
            )

            assert response.status_code == 200

    def test_upload_with_custom_title(self, client, sample_text_file, mock_ingestion_result):
        """Upload with custom title should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text",
                    "title": "My Custom Document Title"
                }
            )

            assert response.status_code == 200

    def test_upload_includes_ingestion_result(self, client, sample_text_file):
        """Upload response should include ingestion result fields."""
        ingestion_result = {
            "chunks_created": 10,
            "document_count": 1
        }
        mock_ingest = AsyncMock(return_value=ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()
            assert "chunks_created" in data
            assert data["chunks_created"] == 10


# =============================================================================
# Validation Tests
# =============================================================================

class TestUploadValidation:
    """Tests for upload request validation."""

    def test_upload_missing_file_returns_422(self, client):
        """Upload without file should return 422."""
        response = client.post(
            "/upload/content",
            data={
                "creator_id": "test-creator-123",
                "content_type": "text"
            }
        )

        assert response.status_code == 422

    def test_upload_missing_content_type_returns_422(self, client, sample_text_file):
        """Upload without content_type should return 422."""
        filename, file_obj, _ = sample_text_file
        response = client.post(
            "/upload/content",
            files={"file": (filename, file_obj)},
            data={
                "creator_id": "test-creator-123"
                # Missing content_type
            }
        )

        assert response.status_code == 422

    def test_upload_missing_creator_id_returns_401(self, client, sample_text_file, mock_ingestion_result):
        """Upload without creator_id and no auth should return 401."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "content_type": "text"
                    # Missing creator_id
                }
            )

            assert response.status_code == 401


# =============================================================================
# Edge Cases
# =============================================================================

class TestUploadEdgeCases:
    """Tests for upload edge cases."""

    def test_upload_empty_file(self, client, mock_ingestion_result):
        """Upload empty file should be handled."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            empty_file = io.BytesIO(b"")
            response = client.post(
                "/upload/content",
                files={"file": ("empty.txt", empty_file, "text/plain")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            # Empty file may still be accepted (ingestion handles it)
            assert response.status_code in [200, 400, 422]

    def test_upload_special_characters_in_filename(self, client, mock_ingestion_result):
        """Upload with special characters in filename should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            content = io.BytesIO(b"test content")
            response = client.post(
                "/upload/content",
                files={"file": ("test file (1) - copy.txt", content, "text/plain")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            assert response.status_code == 200

    def test_upload_unicode_filename(self, client, mock_ingestion_result):
        """Upload with unicode filename should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            content = io.BytesIO(b"test content")
            response = client.post(
                "/upload/content",
                files={"file": ("documento_espanol.txt", content, "text/plain")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            assert response.status_code == 200

    def test_upload_very_long_filename(self, client, mock_ingestion_result):
        """Upload with very long filename should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            long_name = "a" * 200 + ".txt"
            content = io.BytesIO(b"test content")
            response = client.post(
                "/upload/content",
                files={"file": (long_name, content, "text/plain")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            # Long filenames may be truncated but should not fail
            assert response.status_code == 200

    def test_upload_whitespace_only_title(self, client, sample_text_file, mock_ingestion_result):
        """Upload with whitespace-only title should use filename instead."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text",
                    "title": "   "
                }
            )

            assert response.status_code == 200

    def test_upload_calls_ingestion_service(self, client, sample_text_file, mock_ingestion_result):
        """Upload should call ingestion service with correct parameters."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text",
                    "title": "My Document"
                }
            )

            assert response.status_code == 200

            # Verify ingestion was called
            mock_ingest.assert_called_once()
            call_args = mock_ingest.call_args

            # Check parameters
            assert call_args.kwargs["content_type"] == "text"
            assert call_args.kwargs["creator_id"] == "test-creator-123"
            assert "My Document" in str(call_args.kwargs.get("metadata", {}))


# =============================================================================
# Response Format Tests
# =============================================================================

class TestUploadResponseFormat:
    """Tests for upload response format."""

    def test_upload_response_is_json(self, client, sample_text_file, mock_ingestion_result):
        """Upload response should be JSON."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            assert response.headers.get("content-type") == "application/json"
            data = response.json()
            assert isinstance(data, dict)

    def test_upload_response_has_required_fields(self, client, sample_text_file, mock_ingestion_result):
        """Upload response should have all required fields."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            filename, file_obj, content_type = sample_text_file
            response = client.post(
                "/upload/content",
                files={"file": (filename, file_obj, content_type)},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            data = response.json()

            # Required fields
            assert "status" in data
            assert "filename" in data
            assert "creator_id" in data
            assert "content_type" in data


# =============================================================================
# Content Type Tests
# =============================================================================

class TestUploadContentTypes:
    """Tests for different content types."""

    def test_upload_text_content_type(self, client, mock_ingestion_result):
        """Upload with text content type should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            content = io.BytesIO(b"text content")
            response = client.post(
                "/upload/content",
                files={"file": ("test.txt", content, "text/plain")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "text"
                }
            )

            assert response.status_code == 200

    def test_upload_pdf_content_type(self, client, mock_ingestion_result):
        """Upload with pdf content type should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            content = io.BytesIO(b"%PDF-1.4 content")
            response = client.post(
                "/upload/content",
                files={"file": ("test.pdf", content, "application/pdf")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "pdf"
                }
            )

            assert response.status_code == 200

    def test_upload_video_content_type(self, client, mock_ingestion_result):
        """Upload with video content type should work."""
        mock_ingest = AsyncMock(return_value=mock_ingestion_result)

        with patch('main.ingestion_service.ingest_content', mock_ingest):
            content = io.BytesIO(b"video content")
            response = client.post(
                "/upload/content",
                files={"file": ("test.mp4", content, "video/mp4")},
                data={
                    "creator_id": "test-creator-123",
                    "content_type": "video"
                }
            )

            assert response.status_code == 200
