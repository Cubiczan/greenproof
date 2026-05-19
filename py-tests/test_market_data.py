"""
Tests for GreenMarketDataService.

Covers initialization, query methods, mutations, and dashboard aggregation.
"""

from __future__ import annotations

import pytest

from greenverify.models.carbon import (
    CarbonProject,
    CreditNFT,
    DashboardOverview,
    MarketplaceListing,
    ProjectStatus,
    ProjectType,
    RiskLevel,
    VerificationResult,
)
from greenverify.services.market_data import GreenMarketDataService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def service() -> GreenMarketDataService:
    """Create a fresh GreenMarketDataService with seeded demo data."""
    return GreenMarketDataService()


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------

class TestInitialization:
    """Tests for service initialization."""

    def test_service_creates_successfully(self, service: GreenMarketDataService) -> None:
        assert service is not None

    def test_service_seeds_projects(self, service: GreenMarketDataService) -> None:
        projects = service.get_all_projects()
        assert len(projects) == 22

    def test_service_seeds_credits(self, service: GreenMarketDataService) -> None:
        credits = service.get_credits()
        assert len(credits) == 5

    def test_service_seeds_listings(self, service: GreenMarketDataService) -> None:
        listings = service.get_listings()
        assert len(listings) == 3


# ---------------------------------------------------------------------------
# Project query tests
# ---------------------------------------------------------------------------

class TestProjectQueries:
    """Tests for project query methods."""

    def test_get_all_projects_returns_list(self, service: GreenMarketDataService) -> None:
        projects = service.get_all_projects()
        assert isinstance(projects, list)
        assert all(isinstance(p, CarbonProject) for p in projects)

    def test_get_project_valid_id(self, service: GreenMarketDataService) -> None:
        project = service.get_project("proj_001")
        assert project is not None
        assert project.name == "Amazon Rainforest Reforestation Initiative"
        assert project.status == ProjectStatus.VERIFIED

    def test_get_project_invalid_id(self, service: GreenMarketDataService) -> None:
        project = service.get_project("nonexistent_id")
        assert project is None


# ---------------------------------------------------------------------------
# Credit query tests
# ---------------------------------------------------------------------------

class TestCreditQueries:
    """Tests for credit NFT query methods."""

    def test_get_credits_returns_list(self, service: GreenMarketDataService) -> None:
        credits = service.get_credits()
        assert isinstance(credits, list)
        assert all(isinstance(c, CreditNFT) for c in credits)

    def test_get_credit_valid_token_id(self, service: GreenMarketDataService) -> None:
        credit = service.get_credit("nft_001")
        assert credit is not None
        assert credit.project_id == "proj_001"
        assert credit.amount == 45000

    def test_get_credit_invalid_token_id(self, service: GreenMarketDataService) -> None:
        credit = service.get_credit("nonexistent_token")
        assert credit is None


# ---------------------------------------------------------------------------
# Listing query tests
# ---------------------------------------------------------------------------

class TestListingQueries:
    """Tests for marketplace listing query methods."""

    def test_get_listings_returns_list(self, service: GreenMarketDataService) -> None:
        listings = service.get_listings()
        assert isinstance(listings, list)
        assert all(isinstance(l, MarketplaceListing) for l in listings)

    def test_get_listing_valid_id(self, service: GreenMarketDataService) -> None:
        listing = service.get_listing("list_001")
        assert listing is not None
        assert listing.price == 2450.0

    def test_get_listing_invalid_id(self, service: GreenMarketDataService) -> None:
        listing = service.get_listing("nonexistent")
        assert listing is None


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------

class TestDashboard:
    """Tests for dashboard overview computation."""

    def test_get_dashboard_returns_proper_structure(
        self, service: GreenMarketDataService
    ) -> None:
        dashboard = service.get_dashboard_overview()
        assert isinstance(dashboard, DashboardOverview)
        assert dashboard.total_projects == 22
        assert dashboard.active_listings == 3
        assert dashboard.total_credits_verified > 0
        assert dashboard.avg_verification_score >= 0.0

    def test_dashboard_recent_verifications_structure(
        self, service: GreenMarketDataService
    ) -> None:
        dashboard = service.get_dashboard_overview()
        recent = dashboard.recent_verifications
        assert isinstance(recent, list)
        assert len(recent) == 5
        for entry in recent:
            assert "request_id" in entry
            assert "project_id" in entry
            assert "score" in entry
            assert "risk_level" in entry
            assert "pass_fail" in entry


# ---------------------------------------------------------------------------
# Mutation tests
# ---------------------------------------------------------------------------

class TestMutations:
    """Tests for data mutation methods."""

    def test_add_project(self, service: GreenMarketDataService) -> None:
        initial_count = len(service.get_all_projects())
        new_project = CarbonProject(
            name="New Test Project",
            description="A test reforestation project for validation purposes.",
            project_type=ProjectType.REFORESTATION,
            country="France",
            vintage_year=2024,
            estimated_annual_credits=5000,
            credit_standard="VCS",
        )
        result = service.add_project(new_project)
        assert result.project_id == new_project.project_id
        assert len(service.get_all_projects()) == initial_count + 1

    def test_add_listing_valid_token(self, service: GreenMarketDataService) -> None:
        initial_count = len(service.get_listings())
        listing = service.add_listing(token_id="nft_001", price=5000.0)
        assert listing is not None
        assert listing.price == 5000.0
        assert len(service.get_listings()) == initial_count + 1

    def test_add_listing_invalid_token(self, service: GreenMarketDataService) -> None:
        listing = service.add_listing(token_id="nonexistent_nft", price=5000.0)
        assert listing is None

    def test_buy_listing_active(self, service: GreenMarketDataService) -> None:
        listing = service.buy_listing(listing_id="list_001")
        assert listing is not None

    def test_buy_listing_nonexistent(self, service: GreenMarketDataService) -> None:
        result = service.buy_listing(listing_id="nonexistent")
        assert result is None

    def test_buy_listing_already_sold(self, service: GreenMarketDataService) -> None:
        # Buy once
        service.buy_listing(listing_id="list_002")
        # Buy again should return None
        result = service.buy_listing(listing_id="list_002")
        assert result is None

    def test_add_verification(self, service: GreenMarketDataService) -> None:
        result = VerificationResult(
            request_id="req_test_001",
            project_id="proj_001",
            score=90,
            risk_level=RiskLevel.LOW,
            assessment="Excellent project.",
            credit_amount_recommended=40000,
            pass_fail=True,
        )
        stored = service.add_verification(result)
        assert stored.request_id == "req_test_001"
