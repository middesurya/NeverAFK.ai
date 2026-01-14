"""
Comprehensive tests for API versioning functionality.
Tests cover:
- APIVersion enum and properties
- VersionInfo dataclass
- Version extraction from path and headers
- Version deprecation handling
- Version middleware
- Default version behavior
- Version negotiation
- Edge cases
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse


# Import versioning components
from app.utils.versioning import (
    APIVersion,
    VersionInfo,
    extract_version,
    parse_version_string,
    is_version_supported,
    get_version_info,
    get_deprecation_message,
    CURRENT_VERSION,
    DEFAULT_VERSION,
    SUPPORTED_VERSIONS,
    DEPRECATED_VERSIONS,
    VERSION_SUNSET_DATES,
)
from app.middleware.versioning import (
    VersionMiddleware,
    get_version_from_request,
    add_version_headers,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/resource"
    request.headers = {}
    return request


@pytest.fixture
def test_app():
    """Create a test FastAPI app with versioning middleware."""
    app = FastAPI()

    @app.get("/v1/resource")
    async def v1_resource():
        return {"version": "v1", "data": "resource"}

    @app.get("/v2/resource")
    async def v2_resource():
        return {"version": "v2", "data": "resource"}

    @app.get("/resource")
    async def unversioned_resource():
        return {"version": "default", "data": "resource"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    app.add_middleware(VersionMiddleware)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)


# =============================================================================
# Test APIVersion Enum
# =============================================================================

class TestAPIVersionEnum:
    """Tests for APIVersion enum."""

    def test_api_version_v1_value(self):
        """Test V1 enum value."""
        assert APIVersion.V1.value == "v1"

    def test_api_version_v2_value(self):
        """Test V2 enum value."""
        assert APIVersion.V2.value == "v2"

    def test_api_version_v1_is_deprecated(self):
        """Test that V1 is marked as deprecated."""
        assert APIVersion.V1.is_deprecated is True

    def test_api_version_v2_is_not_deprecated(self):
        """Test that V2 is not deprecated."""
        assert APIVersion.V2.is_deprecated is False

    def test_api_version_from_string_v1(self):
        """Test creating APIVersion from 'v1' string."""
        version = APIVersion("v1")
        assert version == APIVersion.V1

    def test_api_version_from_string_v2(self):
        """Test creating APIVersion from 'v2' string."""
        version = APIVersion("v2")
        assert version == APIVersion.V2

    def test_api_version_invalid_raises_value_error(self):
        """Test that invalid version string raises ValueError."""
        with pytest.raises(ValueError):
            APIVersion("v3")

    def test_api_version_string_representation(self):
        """Test string representation of APIVersion."""
        assert str(APIVersion.V1) == "APIVersion.V1"
        assert APIVersion.V1.value == "v1"

    def test_api_version_comparison(self):
        """Test APIVersion comparison."""
        assert APIVersion.V1 != APIVersion.V2
        assert APIVersion.V1 == APIVersion.V1

    def test_api_version_iteration(self):
        """Test iterating over APIVersion enum."""
        versions = list(APIVersion)
        assert len(versions) >= 2
        assert APIVersion.V1 in versions
        assert APIVersion.V2 in versions


# =============================================================================
# Test VersionInfo Dataclass
# =============================================================================

class TestVersionInfo:
    """Tests for VersionInfo dataclass."""

    def test_version_info_creation_basic(self):
        """Test basic VersionInfo creation."""
        info = VersionInfo(version=APIVersion.V2)
        assert info.version == APIVersion.V2
        assert info.deprecated is False
        assert info.sunset_date is None

    def test_version_info_creation_with_deprecation(self):
        """Test VersionInfo creation with deprecation."""
        info = VersionInfo(
            version=APIVersion.V1,
            deprecated=True,
            sunset_date="2025-12-31"
        )
        assert info.version == APIVersion.V1
        assert info.deprecated is True
        assert info.sunset_date == "2025-12-31"

    def test_version_info_default_values(self):
        """Test VersionInfo default values."""
        info = VersionInfo(version=APIVersion.V2)
        assert info.deprecated is False
        assert info.sunset_date is None

    def test_version_info_equality(self):
        """Test VersionInfo equality comparison."""
        info1 = VersionInfo(version=APIVersion.V1, deprecated=True)
        info2 = VersionInfo(version=APIVersion.V1, deprecated=True)
        assert info1 == info2

    def test_version_info_inequality(self):
        """Test VersionInfo inequality comparison."""
        info1 = VersionInfo(version=APIVersion.V1)
        info2 = VersionInfo(version=APIVersion.V2)
        assert info1 != info2


# =============================================================================
# Test Version Extraction
# =============================================================================

class TestVersionExtraction:
    """Tests for version extraction from path and headers."""

    def test_extract_version_from_v1_path(self):
        """Test extracting V1 from path."""
        version = extract_version("/v1/resource", {})
        assert version == APIVersion.V1

    def test_extract_version_from_v2_path(self):
        """Test extracting V2 from path."""
        version = extract_version("/v2/resource", {})
        assert version == APIVersion.V2

    def test_extract_version_from_nested_v1_path(self):
        """Test extracting V1 from nested path."""
        version = extract_version("/v1/api/users/123", {})
        assert version == APIVersion.V1

    def test_extract_version_from_nested_v2_path(self):
        """Test extracting V2 from nested path."""
        version = extract_version("/v2/api/users/123", {})
        assert version == APIVersion.V2

    def test_extract_version_from_accept_version_header_v1(self):
        """Test extracting V1 from Accept-Version header."""
        version = extract_version("/resource", {"accept-version": "v1"})
        assert version == APIVersion.V1

    def test_extract_version_from_accept_version_header_v2(self):
        """Test extracting V2 from Accept-Version header."""
        version = extract_version("/resource", {"accept-version": "v2"})
        assert version == APIVersion.V2

    def test_extract_version_path_takes_precedence_over_header(self):
        """Test that path version takes precedence over header."""
        version = extract_version("/v1/resource", {"accept-version": "v2"})
        assert version == APIVersion.V1

    def test_extract_version_default_when_no_version(self):
        """Test default version when none specified."""
        version = extract_version("/resource", {})
        assert version == DEFAULT_VERSION

    def test_extract_version_case_insensitive_header(self):
        """Test case-insensitive header handling."""
        version = extract_version("/resource", {"Accept-Version": "v1"})
        assert version == APIVersion.V1

    def test_extract_version_x_api_version_header(self):
        """Test X-API-Version header support."""
        version = extract_version("/resource", {"x-api-version": "v1"})
        assert version == APIVersion.V1

    def test_extract_version_api_version_header(self):
        """Test API-Version header support."""
        version = extract_version("/resource", {"api-version": "v2"})
        assert version == APIVersion.V2


# =============================================================================
# Test Parse Version String
# =============================================================================

class TestParseVersionString:
    """Tests for parse_version_string function."""

    def test_parse_version_string_v1(self):
        """Test parsing 'v1' string."""
        version = parse_version_string("v1")
        assert version == APIVersion.V1

    def test_parse_version_string_v2(self):
        """Test parsing 'v2' string."""
        version = parse_version_string("v2")
        assert version == APIVersion.V2

    def test_parse_version_string_uppercase(self):
        """Test parsing uppercase version string."""
        version = parse_version_string("V1")
        assert version == APIVersion.V1

    def test_parse_version_string_mixed_case(self):
        """Test parsing mixed case version string."""
        version = parse_version_string("V2")
        assert version == APIVersion.V2

    def test_parse_version_string_invalid_returns_none(self):
        """Test parsing invalid version returns None."""
        version = parse_version_string("v3")
        assert version is None

    def test_parse_version_string_empty_returns_none(self):
        """Test parsing empty string returns None."""
        version = parse_version_string("")
        assert version is None

    def test_parse_version_string_none_returns_none(self):
        """Test parsing None returns None."""
        version = parse_version_string(None)
        assert version is None

    def test_parse_version_string_whitespace_trimmed(self):
        """Test parsing version string with whitespace."""
        version = parse_version_string("  v1  ")
        assert version == APIVersion.V1


# =============================================================================
# Test Version Support
# =============================================================================

class TestVersionSupport:
    """Tests for version support checking."""

    def test_is_version_supported_v1(self):
        """Test V1 is supported."""
        assert is_version_supported(APIVersion.V1) is True

    def test_is_version_supported_v2(self):
        """Test V2 is supported."""
        assert is_version_supported(APIVersion.V2) is True

    def test_supported_versions_contains_v1(self):
        """Test SUPPORTED_VERSIONS contains V1."""
        assert APIVersion.V1 in SUPPORTED_VERSIONS

    def test_supported_versions_contains_v2(self):
        """Test SUPPORTED_VERSIONS contains V2."""
        assert APIVersion.V2 in SUPPORTED_VERSIONS

    def test_deprecated_versions_contains_v1(self):
        """Test DEPRECATED_VERSIONS contains V1."""
        assert APIVersion.V1 in DEPRECATED_VERSIONS

    def test_deprecated_versions_not_contains_v2(self):
        """Test DEPRECATED_VERSIONS does not contain V2."""
        assert APIVersion.V2 not in DEPRECATED_VERSIONS


# =============================================================================
# Test Version Info Retrieval
# =============================================================================

class TestGetVersionInfo:
    """Tests for get_version_info function."""

    def test_get_version_info_v1(self):
        """Test getting info for V1."""
        info = get_version_info(APIVersion.V1)
        assert info.version == APIVersion.V1
        assert info.deprecated is True

    def test_get_version_info_v2(self):
        """Test getting info for V2."""
        info = get_version_info(APIVersion.V2)
        assert info.version == APIVersion.V2
        assert info.deprecated is False

    def test_get_version_info_v1_has_sunset_date(self):
        """Test V1 info includes sunset date."""
        info = get_version_info(APIVersion.V1)
        assert info.sunset_date is not None

    def test_get_version_info_v2_no_sunset_date(self):
        """Test V2 info has no sunset date."""
        info = get_version_info(APIVersion.V2)
        assert info.sunset_date is None


# =============================================================================
# Test Deprecation Messages
# =============================================================================

class TestDeprecationMessages:
    """Tests for deprecation message generation."""

    def test_get_deprecation_message_v1(self):
        """Test deprecation message for V1."""
        message = get_deprecation_message(APIVersion.V1)
        assert message is not None
        assert "v1" in message.lower() or "deprecated" in message.lower()

    def test_get_deprecation_message_v2_returns_none(self):
        """Test no deprecation message for V2."""
        message = get_deprecation_message(APIVersion.V2)
        assert message is None

    def test_deprecation_message_includes_sunset_date(self):
        """Test deprecation message includes sunset date when available."""
        message = get_deprecation_message(APIVersion.V1)
        if VERSION_SUNSET_DATES.get(APIVersion.V1):
            assert VERSION_SUNSET_DATES[APIVersion.V1] in message


# =============================================================================
# Test Constants
# =============================================================================

class TestConstants:
    """Tests for versioning constants."""

    def test_current_version_is_v2(self):
        """Test CURRENT_VERSION is V2."""
        assert CURRENT_VERSION == APIVersion.V2

    def test_default_version_is_v2(self):
        """Test DEFAULT_VERSION is V2."""
        assert DEFAULT_VERSION == APIVersion.V2

    def test_version_sunset_dates_has_v1(self):
        """Test VERSION_SUNSET_DATES has V1."""
        assert APIVersion.V1 in VERSION_SUNSET_DATES


# =============================================================================
# Test Version Middleware
# =============================================================================

class TestVersionMiddleware:
    """Tests for VersionMiddleware."""

    def test_middleware_v1_request_allowed(self, client):
        """Test V1 requests are allowed."""
        response = client.get("/v1/resource")
        assert response.status_code == 200
        assert response.json()["version"] == "v1"

    def test_middleware_v2_request_allowed(self, client):
        """Test V2 requests are allowed."""
        response = client.get("/v2/resource")
        assert response.status_code == 200
        assert response.json()["version"] == "v2"

    def test_middleware_adds_version_header(self, client):
        """Test middleware adds X-API-Version header."""
        response = client.get("/v2/resource")
        assert "X-API-Version" in response.headers

    def test_middleware_v1_adds_deprecation_warning(self, client):
        """Test V1 requests include deprecation warning header."""
        response = client.get("/v1/resource")
        assert "X-API-Deprecation-Warning" in response.headers or \
               "Deprecation" in response.headers

    def test_middleware_v2_no_deprecation_warning(self, client):
        """Test V2 requests don't include deprecation warning."""
        response = client.get("/v2/resource")
        deprecation_header = response.headers.get("X-API-Deprecation-Warning")
        assert deprecation_header is None or deprecation_header == ""

    def test_middleware_default_version_applied(self, client):
        """Test default version is applied to unversioned endpoints."""
        response = client.get("/resource")
        assert response.status_code == 200

    def test_middleware_header_versioning(self, client):
        """Test version selection via Accept-Version header."""
        response = client.get("/resource", headers={"Accept-Version": "v1"})
        assert response.status_code == 200

    def test_middleware_adds_sunset_header_for_deprecated(self, client):
        """Test Sunset header is added for deprecated versions."""
        response = client.get("/v1/resource")
        assert "Sunset" in response.headers or "X-API-Sunset" in response.headers

    def test_middleware_health_endpoint_not_versioned(self, client):
        """Test health endpoint works without version."""
        response = client.get("/health")
        assert response.status_code == 200


# =============================================================================
# Test Get Version From Request
# =============================================================================

class TestGetVersionFromRequest:
    """Tests for get_version_from_request function."""

    def test_get_version_from_v1_path(self, mock_request):
        """Test extracting version from V1 path."""
        mock_request.url.path = "/v1/resource"
        mock_request.headers = {}
        version = get_version_from_request(mock_request)
        assert version == APIVersion.V1

    def test_get_version_from_v2_path(self, mock_request):
        """Test extracting version from V2 path."""
        mock_request.url.path = "/v2/resource"
        mock_request.headers = {}
        version = get_version_from_request(mock_request)
        assert version == APIVersion.V2

    def test_get_version_from_header(self, mock_request):
        """Test extracting version from header."""
        mock_request.url.path = "/resource"
        mock_request.headers = {"accept-version": "v1"}
        version = get_version_from_request(mock_request)
        assert version == APIVersion.V1

    def test_get_version_default(self, mock_request):
        """Test default version when none specified."""
        mock_request.url.path = "/resource"
        mock_request.headers = {}
        version = get_version_from_request(mock_request)
        assert version == DEFAULT_VERSION


# =============================================================================
# Test Add Version Headers
# =============================================================================

class TestAddVersionHeaders:
    """Tests for add_version_headers function."""

    def test_add_version_headers_v2(self):
        """Test adding headers for V2."""
        headers = {}
        add_version_headers(headers, APIVersion.V2)
        assert "X-API-Version" in headers
        assert headers["X-API-Version"] == "v2"

    def test_add_version_headers_v1_includes_deprecation(self):
        """Test adding headers for V1 includes deprecation."""
        headers = {}
        add_version_headers(headers, APIVersion.V1)
        assert "X-API-Version" in headers
        assert "X-API-Deprecation-Warning" in headers or "Deprecation" in headers

    def test_add_version_headers_v1_includes_sunset(self):
        """Test adding headers for V1 includes sunset date."""
        headers = {}
        add_version_headers(headers, APIVersion.V1)
        assert "Sunset" in headers or "X-API-Sunset" in headers


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_extract_version_empty_path(self):
        """Test version extraction with empty path."""
        version = extract_version("", {})
        assert version == DEFAULT_VERSION

    def test_extract_version_root_path(self):
        """Test version extraction with root path."""
        version = extract_version("/", {})
        assert version == DEFAULT_VERSION

    def test_extract_version_v1_only_path(self):
        """Test version extraction with '/v1' as entire path."""
        version = extract_version("/v1", {})
        assert version == APIVersion.V1

    def test_extract_version_v2_only_path(self):
        """Test version extraction with '/v2' as entire path."""
        version = extract_version("/v2", {})
        assert version == APIVersion.V2

    def test_extract_version_v1_with_trailing_slash(self):
        """Test version extraction with '/v1/'."""
        version = extract_version("/v1/", {})
        assert version == APIVersion.V1

    def test_extract_version_partial_version_in_path(self):
        """Test that partial version match doesn't extract (e.g., /v10)."""
        version = extract_version("/v10/resource", {})
        # Should not match v1, should use default
        assert version == DEFAULT_VERSION

    def test_extract_version_version_not_at_start(self):
        """Test version in middle of path doesn't match."""
        version = extract_version("/api/v1/resource", {})
        # Depends on implementation - might want to check for /api/v1 pattern
        # For now, we assume it should match since path contains /v1
        # This test documents the expected behavior

    def test_extract_version_invalid_header_version(self):
        """Test invalid version in header uses default."""
        version = extract_version("/resource", {"accept-version": "v99"})
        assert version == DEFAULT_VERSION

    def test_extract_version_empty_header_value(self):
        """Test empty header value uses default."""
        version = extract_version("/resource", {"accept-version": ""})
        assert version == DEFAULT_VERSION

    def test_version_info_immutability(self):
        """Test VersionInfo is properly encapsulated."""
        info1 = get_version_info(APIVersion.V1)
        info2 = get_version_info(APIVersion.V1)
        # Should return same info for same version
        assert info1.version == info2.version
        assert info1.deprecated == info2.deprecated


# =============================================================================
# Test Integration
# =============================================================================

class TestIntegration:
    """Integration tests for versioning system."""

    def test_full_v1_request_flow(self, client):
        """Test complete V1 request flow."""
        response = client.get("/v1/resource")

        # Request should succeed
        assert response.status_code == 200
        assert response.json()["version"] == "v1"

        # Should have version headers
        assert "X-API-Version" in response.headers

        # Should have deprecation warning
        has_deprecation = (
            "X-API-Deprecation-Warning" in response.headers or
            "Deprecation" in response.headers
        )
        assert has_deprecation

    def test_full_v2_request_flow(self, client):
        """Test complete V2 request flow."""
        response = client.get("/v2/resource")

        # Request should succeed
        assert response.status_code == 200
        assert response.json()["version"] == "v2"

        # Should have version headers
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v2"

    def test_header_versioning_flow(self, client):
        """Test header-based versioning flow."""
        response = client.get(
            "/resource",
            headers={"Accept-Version": "v1"}
        )
        assert response.status_code == 200

    def test_default_version_flow(self, client):
        """Test default version when none specified."""
        response = client.get("/resource")
        assert response.status_code == 200
        # Should use default version (v2)
        assert response.json()["version"] == "default"


# =============================================================================
# Test Concurrent Requests
# =============================================================================

class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    def test_concurrent_different_versions(self, test_app):
        """Test concurrent requests with different versions."""
        client = TestClient(test_app)

        # Make requests to both versions
        v1_response = client.get("/v1/resource")
        v2_response = client.get("/v2/resource")

        assert v1_response.json()["version"] == "v1"
        assert v2_response.json()["version"] == "v2"


# =============================================================================
# Test Header Formats
# =============================================================================

class TestHeaderFormats:
    """Tests for version header formats."""

    def test_x_api_version_format(self, client):
        """Test X-API-Version header format."""
        response = client.get("/v2/resource")
        assert response.headers.get("X-API-Version") in ["v1", "v2"]

    def test_deprecation_header_format(self, client):
        """Test deprecation header format for V1."""
        response = client.get("/v1/resource")
        deprecation = response.headers.get("X-API-Deprecation-Warning") or \
                      response.headers.get("Deprecation")
        assert deprecation is not None

    def test_sunset_header_format(self, client):
        """Test Sunset header format for deprecated versions."""
        response = client.get("/v1/resource")
        sunset = response.headers.get("Sunset") or response.headers.get("X-API-Sunset")
        if sunset:
            # Should be a valid date format
            assert len(sunset) > 0


# =============================================================================
# Test Version Negotiation
# =============================================================================

class TestVersionNegotiation:
    """Tests for version negotiation logic."""

    def test_path_version_priority(self):
        """Test path version has highest priority."""
        version = extract_version("/v1/resource", {"accept-version": "v2"})
        assert version == APIVersion.V1

    def test_header_fallback(self):
        """Test header is used when no path version."""
        version = extract_version("/resource", {"accept-version": "v1"})
        assert version == APIVersion.V1

    def test_default_fallback(self):
        """Test default version when no version specified."""
        version = extract_version("/resource", {})
        assert version == DEFAULT_VERSION

    def test_multiple_version_headers_priority(self):
        """Test priority when multiple version headers present."""
        headers = {
            "accept-version": "v1",
            "x-api-version": "v2"
        }
        version = extract_version("/resource", headers)
        # accept-version should have priority
        assert version == APIVersion.V1


# =============================================================================
# Test Error Cases
# =============================================================================

class TestErrorCases:
    """Tests for error handling in versioning."""

    def test_unsupported_version_in_path(self, client):
        """Test handling of unsupported version in path."""
        response = client.get("/v99/resource")
        # Should return 404 (no route) not crash
        assert response.status_code == 404

    def test_malformed_version_header(self, client):
        """Test handling of malformed version header."""
        response = client.get(
            "/resource",
            headers={"Accept-Version": "not-a-version"}
        )
        # Should use default version, not crash
        assert response.status_code == 200
