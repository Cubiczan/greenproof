"""
Tests for GreenVerify AI FastAPI routes.

Uses FastAPI TestClient with mocked QwenClient so tests don't need API keys.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from greenverify.api import create_app
from greenverify.services.market_data import GreenMarketDataService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def data_service() -> GreenMarketDataService:
    """Create a fresh GreenMarketDataService for each test."""
    return GreenMarketDataService()


@pytest.fixture()
def client(data_service: GreenMarketDataService) -> TestClient:
    """Create a FastAPI TestClient with a real data service but no LLM."""
    app = create_app(market_data=data_service)
    return TestClient(app)


MOCK_LLM_RESULT = {
    "score": 85,
    "risk_level": "Low",
    "assessment": (
        "The project demonstrates strong additionality and measurable "
        "emission reductions. Documentation is thorough and methodology "
        "is appropriately applied."
    ),
    "recommendations": [
        "Expand monitoring coverage",
        "Consider CCB certification",
    ],
    "recommended_credit_amount": 9000,
    "pass_fail": True,
}

VALID_VERIFY_FORM = {
    "name": "Test Reforestation Project",
    "description": "A reforestation project that plants native trees on degraded land.",
    "project_type": "Reforestation",
    "country": "Brazil",
    "vintage_year": 2024,
    "estimated_credits": 10000,
    "credit_standard": "VCS",
    "documentation_text": (
        "Project Documentation for Test Reforestation Project\n\n"
        "1. Project Description\n"
        "This project involves reforesting 500 hectares of degraded land "
        "in the state of Pará, Brazil. Native species including Brazil nut "
        "and Ipê will be planted. The project follows VCS methodology AR-ACM0003 "
        "and has third-party monitoring by SGS.\n\n"
        "2. Additionality\n"
        "Without this project, the degraded land would remain unproductive "
        "and continue to emit CO2 through soil degradation. Baseline scenario "
        "shows no natural regeneration expected within 30 years.\n\n"
        "3. Monitoring Plan\n"
        "Annual monitoring using satellite imagery and ground surveys. "
        "Tree survival rates and carbon stock measurements recorded quarterly."
    ),
}


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_status_healthy(self, client: TestClient) -> None:
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_version(self, client: TestClient) -> None:
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_returns_timestamp(self, client: TestClient) -> None:
        response = client.get("/api/health")
        data = response.json()
        assert "timestamp" in data
        assert data["timestamp"] is not None


# ---------------------------------------------------------------------------
# Dashboard endpoint tests
# ---------------------------------------------------------------------------

class TestDashboardEndpoint:
    """Tests for GET /api/dashboard."""

    def test_dashboard_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/dashboard")
        assert response.status_code == 200

    def test_dashboard_returns_proper_structure(self, client: TestClient) -> None:
        response = client.get("/api/dashboard")
        data = response.json()
        assert "total_credits_verified" in data
        assert "total_credits_traded" in data
        assert "total_projects" in data
        assert "active_listings" in data
        assert "avg_verification_score" in data
        assert "recent_verifications" in data

    def test_dashboard_total_projects(self, client: TestClient) -> None:
        response = client.get("/api/dashboard")
        data = response.json()
        assert data["total_projects"] == 22

    def test_dashboard_active_listings(self, client: TestClient) -> None:
        response = client.get("/api/dashboard")
        data = response.json()
        assert data["active_listings"] == 3


# ---------------------------------------------------------------------------
# Projects endpoint tests
# ---------------------------------------------------------------------------

class TestProjectsEndpoint:
    """Tests for GET /api/projects and GET /api/projects/{id}."""

    def test_list_projects_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/projects")
        assert response.status_code == 200

    def test_list_projects_returns_list(self, client: TestClient) -> None:
        response = client.get("/api/projects")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 22

    def test_get_project_valid_id(self, client: TestClient) -> None:
        response = client.get("/api/projects/proj_001")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "proj_001"
        assert data["name"] == "Amazon Rainforest Reforestation Initiative"

    def test_get_project_invalid_id(self, client: TestClient) -> None:
        response = client.get("/api/projects/nonexistent_id")
        assert response.status_code == 404

    def test_projects_have_required_fields(self, client: TestClient) -> None:
        response = client.get("/api/projects")
        data = response.json()
        for project in data:
            assert "project_id" in project
            assert "name" in project
            assert "project_type" in project
            assert "country" in project
            assert "vintage_year" in project


# ---------------------------------------------------------------------------
# Credits endpoint tests
# ---------------------------------------------------------------------------

class TestCreditsEndpoint:
    """Tests for GET /api/credits."""

    def test_list_credits_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/credits")
        assert response.status_code == 200

    def test_list_credits_returns_list(self, client: TestClient) -> None:
        response = client.get("/api/credits")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_credits_have_required_fields(self, client: TestClient) -> None:
        response = client.get("/api/credits")
        data = response.json()
        for credit in data:
            assert "token_id" in credit
            assert "project_id" in credit
            assert "amount" in credit
            assert "owner" in credit


# ---------------------------------------------------------------------------
# Marketplace endpoint tests
# ---------------------------------------------------------------------------

class TestMarketplaceEndpoint:
    """Tests for GET /api/marketplace."""

    def test_list_marketplace_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/marketplace")
        assert response.status_code == 200

    def test_list_marketplace_returns_list(self, client: TestClient) -> None:
        response = client.get("/api/marketplace")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_marketplace_listings_have_required_fields(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/marketplace")
        data = response.json()
        for listing in data:
            assert "listing_id" in listing
            assert "token_id" in listing
            assert "price" in listing
            assert "seller" in listing
            assert "status" in listing


# ---------------------------------------------------------------------------
# Verification endpoint tests
# ---------------------------------------------------------------------------

class TestVerifyEndpoint:
    """Tests for POST /api/verify with mocked QwenClient."""

    def test_verify_returns_200_with_mock(self, client: TestClient) -> None:
        """Test that POST /api/verify works when QwenClient is mocked."""
        with patch("greenverify.engines.verifier.QwenClient") as mock_qwen_cls:
            mock_instance = MagicMock()
            mock_instance.verify_carbon_project = AsyncMock(
                return_value=MOCK_LLM_RESULT
            )
            mock_qwen_cls.return_value = mock_instance

            response = client.post("/api/verify", json=VALID_VERIFY_FORM)
            assert response.status_code == 200

    def test_verify_returns_result_structure(self, client: TestClient) -> None:
        """Test that verification result has expected fields."""
        with patch("greenverify.engines.verifier.QwenClient") as mock_qwen_cls:
            mock_instance = MagicMock()
            mock_instance.verify_carbon_project = AsyncMock(
                return_value=MOCK_LLM_RESULT
            )
            mock_qwen_cls.return_value = mock_instance

            response = client.post("/api/verify", json=VALID_VERIFY_FORM)
            data = response.json()
            assert "request_id" in data
            assert "project_id" in data
            assert "score" in data
            assert "risk_level" in data
            assert "assessment" in data
            assert "recommendations" in data
            assert "pass_fail" in data

    def test_verify_score_matches_mock(self, client: TestClient) -> None:
        """Test that the score from the mock LLM is returned correctly."""
        with patch("greenverify.engines.verifier.QwenClient") as mock_qwen_cls:
            mock_instance = MagicMock()
            mock_instance.verify_carbon_project = AsyncMock(
                return_value=MOCK_LLM_RESULT
            )
            mock_qwen_cls.return_value = mock_instance

            response = client.post("/api/verify", json=VALID_VERIFY_FORM)
            data = response.json()
            assert data["score"] == 85
            assert data["pass_fail"] is True

    def test_verify_invalid_form_data(self, client: TestClient) -> None:
        """Test that invalid form data returns 422."""
        invalid_form = {
            "name": "",
            "description": "Short",
            "project_type": "Reforestation",
            "country": "Brazil",
            "vintage_year": 2024,
            "estimated_credits": 10000,
            "credit_standard": "VCS",
            "documentation_text": "Too short",
        }
        response = client.post("/api/verify", json=invalid_form)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Marketplace listing / buying tests
# ---------------------------------------------------------------------------

class TestMarketplaceOperations:
    """Tests for POST /api/marketplace/list and POST /api/marketplace/buy."""

    def test_create_listing_valid_token(self, client: TestClient) -> None:
        response = client.post(
            "/api/marketplace/list",
            json={"token_id": "nft_003", "price": 3000.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_id"] == "nft_003"
        assert data["price"] == 3000.0

    def test_create_listing_invalid_token(self, client: TestClient) -> None:
        response = client.post(
            "/api/marketplace/list",
            json={"token_id": "nonexistent_nft", "price": 1000.0},
        )
        assert response.status_code == 404

    def test_create_listing_invalid_price(self, client: TestClient) -> None:
        response = client.post(
            "/api/marketplace/list",
            json={"token_id": "nft_001", "price": -100.0},
        )
        assert response.status_code == 422

    def test_buy_listing_valid(self, client: TestClient) -> None:
        response = client.post(
            "/api/marketplace/buy",
            json={"listing_id": "list_001"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Sold"

    def test_buy_listing_already_sold(self, client: TestClient) -> None:
        # Buy once
        client.post("/api/marketplace/buy", json={"listing_id": "list_002"})
        # Buy again should fail
        response = client.post(
            "/api/marketplace/buy",
            json={"listing_id": "list_002"},
        )
        assert response.status_code == 404

    def test_buy_listing_nonexistent(self, client: TestClient) -> None:
        response = client.post(
            "/api/marketplace/buy",
            json={"listing_id": "nonexistent_listing"},
        )
        assert response.status_code == 404
