"""
PRD-004: Integration Tests for API Endpoints - Health Check Tests

Tests for GET /health endpoint:
- AC-5: GET /health returns 200 with status

These tests verify the health check endpoint works correctly in different modes.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Tests for GET /health endpoint - AC-5."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_field(self, client):
        """Health endpoint should return status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_returns_database_field(self, client):
        """Health endpoint should return database connection status."""
        response = client.get("/health")
        data = response.json()
        assert "database" in data
        # Should be either 'connected' or 'local_mode'
        assert data["database"] in ["connected", "local_mode"]

    def test_health_returns_mode_field(self, client):
        """Health endpoint should return mode field."""
        response = client.get("/health")
        data = response.json()
        assert "mode" in data
        # Should be either 'production' or 'development'
        assert data["mode"] in ["production", "development"]

    def test_health_mode_matches_database_status(self, client):
        """Mode should match database connection status."""
        response = client.get("/health")
        data = response.json()

        if data["database"] == "connected":
            assert data["mode"] == "production"
        else:
            assert data["mode"] == "development"

    def test_health_endpoint_is_fast(self, client):
        """Health endpoint should respond quickly (< 1 second)."""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0

    def test_health_returns_json(self, client):
        """Health endpoint should return valid JSON."""
        response = client.get("/health")
        assert response.headers.get("content-type") == "application/json"
        # Should not raise JSONDecodeError
        data = response.json()
        assert isinstance(data, dict)


class TestHealthWithMockedDatabase:
    """Tests for health endpoint with mocked database states."""

    def test_health_with_connected_database(self, client):
        """Health should show connected when database is available."""
        with patch('main.db') as mock_db:
            mock_db.is_connected.return_value = True
            response = client.get("/health")
            data = response.json()

            assert response.status_code == 200
            assert data["database"] == "connected"
            assert data["mode"] == "production"

    def test_health_with_disconnected_database(self, client):
        """Health should show local_mode when database is unavailable."""
        with patch('main.db') as mock_db:
            mock_db.is_connected.return_value = False
            response = client.get("/health")
            data = response.json()

            assert response.status_code == 200
            assert data["database"] == "local_mode"
            assert data["mode"] == "development"


class TestRootEndpoint:
    """Tests for GET / root endpoint."""

    def test_root_returns_200(self, client):
        """Root endpoint should return 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self, client):
        """Root endpoint should return API information."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "Creator Support AI API" in data["message"]

    def test_root_returns_status(self, client):
        """Root endpoint should return running status."""
        response = client.get("/")
        data = response.json()

        assert "status" in data
        assert data["status"] == "running"

    def test_root_returns_json(self, client):
        """Root endpoint should return valid JSON."""
        response = client.get("/")
        assert response.headers.get("content-type") == "application/json"
        data = response.json()
        assert isinstance(data, dict)
