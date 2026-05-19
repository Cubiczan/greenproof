"""
Tests for GreenVerify AI Pydantic models.

Covers model creation, validation, enum values, and edge cases.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from greenverify.models.carbon import (
    CarbonProject,
    CreditNFT,
    DashboardOverview,
    MarketplaceListing,
    ProjectStatus,
    ProjectType,
    RiskLevel,
    VerificationFormData,
    VerificationResult,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------

class TestEnums:
    """Tests for enumeration types."""

    def test_project_type_values(self) -> None:
        assert ProjectType.REFORESTATION.value == "Reforestation"
        assert ProjectType.RENEWABLE_ENERGY.value == "RenewableEnergy"
        assert ProjectType.METHANE_CAPTURE.value == "MethaneCapture"
        assert ProjectType.INDUSTRIAL.value == "Industrial"

    def test_project_status_values(self) -> None:
        assert ProjectStatus.PENDING.value == "Pending"
        assert ProjectStatus.VERIFYING.value == "Verifying"
        assert ProjectStatus.VERIFIED.value == "Verified"
        assert ProjectStatus.REJECTED.value == "Rejected"

    def test_risk_level_values(self) -> None:
        assert RiskLevel.LOW.value == "Low"
        assert RiskLevel.MEDIUM.value == "Medium"
        assert RiskLevel.HIGH.value == "High"
        assert RiskLevel.CRITICAL.value == "Critical"

    def test_project_type_enum_count(self) -> None:
        assert len(ProjectType) == 4

    def test_project_status_enum_count(self) -> None:
        assert len(ProjectStatus) == 4

    def test_risk_level_enum_count(self) -> None:
        assert len(RiskLevel) == 4


# ---------------------------------------------------------------------------
# CarbonProject tests
# ---------------------------------------------------------------------------

class TestCarbonProject:
    """Tests for CarbonProject model."""

    def test_create_carbon_project_with_valid_data(self) -> None:
        project = CarbonProject(
            name="Test Forest",
            description="A test reforestation project for validation purposes.",
            project_type=ProjectType.REFORESTATION,
            country="Brazil",
            vintage_year=2023,
            estimated_annual_credits=10000,
            credit_standard="VCS",
        )
        assert project.name == "Test Forest"
        assert project.project_type == ProjectType.REFORESTATION
        assert project.country == "Brazil"
        assert project.vintage_year == 2023
        assert project.estimated_annual_credits == 10000
        assert project.credit_standard == "VCS"
        assert project.status == ProjectStatus.PENDING
        assert project.documentation_urls == []
        assert project.verified_at is None

    def test_carbon_project_generates_id(self) -> None:
        project = CarbonProject(
            name="Test",
            description="A test reforestation project for validation.",
            project_type=ProjectType.RENEWABLE_ENERGY,
            country="Germany",
            vintage_year=2024,
            estimated_annual_credits=5000,
            credit_standard="Gold Standard",
        )
        assert project.project_id is not None
        assert len(project.project_id) > 0

    def test_carbon_project_custom_id(self) -> None:
        project = CarbonProject(
            project_id="custom_123",
            name="Test",
            description="A test reforestation project for validation.",
            project_type=ProjectType.METHANE_CAPTURE,
            country="USA",
            vintage_year=2023,
            estimated_annual_credits=8000,
            credit_standard="VCS",
        )
        assert project.project_id == "custom_123"

    def test_carbon_project_vintage_year_too_low(self) -> None:
        with pytest.raises(ValidationError):
            CarbonProject(
                name="Test",
                description="A test reforestation project for validation.",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=1999,
                estimated_annual_credits=1000,
                credit_standard="VCS",
            )

    def test_carbon_project_negative_credits(self) -> None:
        with pytest.raises(ValidationError):
            CarbonProject(
                name="Test",
                description="A test reforestation project for validation.",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=2023,
                estimated_annual_credits=-1,
                credit_standard="VCS",
            )


# ---------------------------------------------------------------------------
# VerificationResult tests
# ---------------------------------------------------------------------------

class TestVerificationResult:
    """Tests for VerificationResult model."""

    def test_create_verification_result_pass(self) -> None:
        result = VerificationResult(
            request_id="req_001",
            project_id="proj_001",
            score=85,
            risk_level=RiskLevel.LOW,
            assessment="This project demonstrates strong additionality.",
            recommendations=["Expand buffer zone"],
            credit_amount_recommended=40000,
            pass_fail=True,
        )
        assert result.score == 85
        assert result.risk_level == RiskLevel.LOW
        assert result.pass_fail is True
        assert len(result.recommendations) == 1

    def test_verification_result_score_clamped_high(self) -> None:
        with pytest.raises(ValidationError):
            VerificationResult(
                request_id="req_002",
                project_id="proj_002",
                score=101,
                risk_level=RiskLevel.MEDIUM,
                assessment="Test assessment.",
                credit_amount_recommended=1000,
                pass_fail=False,
            )

    def test_verification_result_score_clamped_low(self) -> None:
        with pytest.raises(ValidationError):
            VerificationResult(
                request_id="req_003",
                project_id="proj_003",
                score=-1,
                risk_level=RiskLevel.HIGH,
                assessment="Test assessment.",
                credit_amount_recommended=1000,
                pass_fail=False,
            )


# ---------------------------------------------------------------------------
# CreditNFT tests
# ---------------------------------------------------------------------------

class TestCreditNFT:
    """Tests for CreditNFT model."""

    def test_create_credit_nft(self) -> None:
        nft = CreditNFT(
            token_id="nft_001",
            project_id="proj_001",
            owner="0xSeller123",
            amount=45000,
            vintage_year=2023,
            credit_standard="VCS",
            project_name="Amazon Reforestation",
            project_type=ProjectType.REFORESTATION,
            country="Brazil",
            minted_at="2023-08-21T10:00:00Z",
            onchain_tx_hash="0xabc123",
        )
        assert nft.token_id == "nft_001"
        assert nft.amount == 45000
        assert nft.project_type == ProjectType.REFORESTATION


# ---------------------------------------------------------------------------
# MarketplaceListing tests
# ---------------------------------------------------------------------------

class TestMarketplaceListing:
    """Tests for MarketplaceListing model."""

    def test_create_marketplace_listing_defaults(self) -> None:
        listing = MarketplaceListing(
            token_id="nft_001",
            seller="0xSeller123",
            price=1000.0,
        )
        assert listing.token_id == "nft_001"
        assert listing.price == 1000.0
        assert listing.listing_id is not None
        assert len(listing.listing_id) > 0

    def test_marketplace_listing_negative_price(self) -> None:
        with pytest.raises(ValidationError):
            MarketplaceListing(
                token_id="nft_001",
                seller="0xSeller123",
                price=-50.0,
            )


# ---------------------------------------------------------------------------
# DashboardOverview tests
# ---------------------------------------------------------------------------

class TestDashboardOverview:
    """Tests for DashboardOverview model."""

    def test_create_dashboard_overview(self) -> None:
        dashboard = DashboardOverview(
            total_credits_verified=181000,
            total_credits_traded=0,
            total_projects=22,
            active_listings=3,
            avg_verification_score=84.4,
            recent_verifications=[{"request_id": "req_001", "project_id": "proj_001"}],
        )
        assert dashboard.total_projects == 22
        assert dashboard.active_listings == 3
        assert dashboard.avg_verification_score == 84.4
        assert len(dashboard.recent_verifications) == 1

    def test_dashboard_overview_defaults(self) -> None:
        dashboard = DashboardOverview(
            total_credits_verified=100,
            total_credits_traded=0,
            total_projects=5,
            active_listings=2,
            avg_verification_score=80.0,
        )
        assert dashboard.recent_verifications == []


# ---------------------------------------------------------------------------
# VerificationFormData tests
# ---------------------------------------------------------------------------

class TestVerificationFormData:
    """Tests for VerificationFormData model with validation."""

    def test_valid_form_data(self) -> None:
        form = VerificationFormData(
            name="Test Project",
            description="A test reforestation project for validation purposes.",
            project_type=ProjectType.REFORESTATION,
            country="Brazil",
            vintage_year=2023,
            estimated_credits=10000,
            credit_standard="VCS",
            documentation_text="A" * 50,  # min_length=50
        )
        assert form.name == "Test Project"
        assert form.project_type == ProjectType.REFORESTATION

    def test_form_data_name_empty(self) -> None:
        with pytest.raises(ValidationError):
            VerificationFormData(
                name="",
                description="A test reforestation project for validation purposes.",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=2023,
                estimated_credits=10000,
                credit_standard="VCS",
                documentation_text="A" * 50,
            )

    def test_form_data_description_too_short(self) -> None:
        with pytest.raises(ValidationError):
            VerificationFormData(
                name="Test",
                description="Short",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=2023,
                estimated_credits=10000,
                credit_standard="VCS",
                documentation_text="A" * 50,
            )

    def test_form_data_documentation_too_short(self) -> None:
        with pytest.raises(ValidationError):
            VerificationFormData(
                name="Test",
                description="A test reforestation project for validation purposes.",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=2023,
                estimated_credits=10000,
                credit_standard="VCS",
                documentation_text="Too short",
            )

    def test_form_data_negative_estimated_credits(self) -> None:
        with pytest.raises(ValidationError):
            VerificationFormData(
                name="Test",
                description="A test reforestation project for validation purposes.",
                project_type=ProjectType.REFORESTATION,
                country="Brazil",
                vintage_year=2023,
                estimated_credits=-1,
                credit_standard="VCS",
                documentation_text="A" * 50,
            )
