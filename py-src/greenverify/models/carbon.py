"""
Pydantic v2 data models for GreenVerify AI.

Defines the complete schema for carbon credit projects, verification
workflows, credit NFTs, marketplace listings, and dashboard aggregates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProjectType(str, Enum):
    """Supported carbon credit project categories."""
    REFORESTATION = "Reforestation"
    RENEWABLE_ENERGY = "RenewableEnergy"
    METHANE_CAPTURE = "MethaneCapture"
    INDUSTRIAL = "Industrial"


class ProjectStatus(str, Enum):
    """Lifecycle states for a carbon credit project."""
    PENDING = "Pending"
    VERIFYING = "Verifying"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


class RiskLevel(str, Enum):
    """Risk classification levels from verification assessment."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ListingStatus(str, Enum):
    """States for a marketplace listing."""
    ACTIVE = "Active"
    SOLD = "Sold"
    CANCELLED = "Cancelled"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class CarbonProject(BaseModel):
    """A carbon credit project submitted for verification or already verified.

    Attributes:
        project_id: Unique identifier for the project.
        name: Human-readable project name.
        description: Detailed project description.
        project_type: Category of carbon credit project.
        country: Country where the project is located.
        vintage_year: The reporting year for the credits.
        estimated_annual_credits: Expected credits in tonnes CO2e per year.
        credit_standard: Certification standard (e.g. VCS, Gold Standard).
        documentation_urls: List of URLs to supporting documentation.
        status: Current lifecycle status of the project.
        submitted_at: ISO-8601 timestamp of project submission.
        verified_at: ISO-8601 timestamp of successful verification, if any.
    """

    project_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    description: str
    project_type: ProjectType
    country: str
    vintage_year: int = Field(ge=2000, le=2035)
    estimated_annual_credits: int = Field(ge=0, description="Tonnes CO2e per year")
    credit_standard: str
    documentation_urls: list[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.PENDING
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verified_at: str | None = None


class VerificationRequest(BaseModel):
    """A request to verify a specific carbon credit project.

    Attributes:
        request_id: Unique identifier for this verification request.
        project: The carbon project to be verified.
        verifier_id: Identifier of the entity performing verification.
        submitted_at: ISO-8601 timestamp of request submission.
    """

    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    project: CarbonProject
    verifier_id: str = Field(default="greenverify-ai-agent")
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class VerificationResult(BaseModel):
    """Outcome of an AI-powered carbon credit verification assessment.

    Attributes:
        request_id: Correlates back to the originating VerificationRequest.
        project_id: Identifier of the verified project.
        score: Overall verification score from 0 to 100.
        risk_level: Classified risk level of the project.
        assessment: Detailed narrative assessment from the AI verifier.
        recommendations: List of actionable improvement recommendations.
        credit_amount_recommended: Verified credit amount in tonnes CO2e.
        pass_fail: Whether the project passes verification.
        verified_at: ISO-8601 timestamp of verification completion.
    """

    request_id: str
    project_id: str
    score: int = Field(ge=0, le=100, description="Verification score 0-100")
    risk_level: RiskLevel
    assessment: str
    recommendations: list[str] = Field(default_factory=list)
    credit_amount_recommended: int = Field(
        ge=0, description="Recommended verified credits in tonnes CO2e"
    )
    pass_fail: bool
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CreditNFT(BaseModel):
    """An on-chain carbon credit represented as an NFT token.

    Attributes:
        token_id: Unique on-chain token identifier.
        project_id: Associated carbon credit project.
        owner: Current owner wallet address.
        amount: Credit amount in tonnes CO2e.
        vintage_year: Reporting year for these credits.
        credit_standard: Certification standard.
        project_name: Name of the originating project.
        project_type: Category of the originating project.
        country: Country of the originating project.
        minted_at: ISO-8601 timestamp of NFT minting.
        onchain_tx_hash: Transaction hash of the minting transaction.
    """

    token_id: str
    project_id: str
    owner: str
    amount: int = Field(ge=0, description="Tonnes CO2e")
    vintage_year: int
    credit_standard: str
    project_name: str
    project_type: ProjectType
    country: str
    minted_at: str
    onchain_tx_hash: str


class MarketplaceListing(BaseModel):
    """A listing of a carbon credit NFT on the trading marketplace.

    Attributes:
        listing_id: Unique identifier for the listing.
        token_id: The credit NFT being sold.
        seller: Seller's wallet address.
        price: Listing price in POT tokens.
        listed_at: ISO-8601 timestamp of listing creation.
        status: Current state of the listing.
    """

    listing_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    token_id: str
    seller: str
    price: float = Field(ge=0, description="Price in POT tokens")
    listed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: ListingStatus = ListingStatus.ACTIVE


class DashboardOverview(BaseModel):
    """Aggregated dashboard metrics for the GreenVerify platform.

    Attributes:
        total_credits_verified: Sum of all verified credits in tonnes CO2e.
        total_credits_traded: Sum of credits that have been traded.
        total_projects: Total number of registered projects.
        active_listings: Number of currently active marketplace listings.
        avg_verification_score: Average verification score across all projects.
        recent_verifications: List of recent verification result summaries.
    """

    total_credits_verified: int
    total_credits_traded: int
    total_projects: int
    active_listings: int
    avg_verification_score: float
    recent_verifications: list[dict[str, Any]] = Field(default_factory=list)


class VerificationFormData(BaseModel):
    """Form payload for submitting a new carbon project for verification.

    This is the input schema for the ``POST /api/verify`` endpoint.

    Attributes:
        name: Project name.
        description: Detailed project description.
        project_type: Category of the carbon credit project.
        country: Country where the project is located.
        vintage_year: Reporting year for the credits.
        estimated_credits: Expected annual credits in tonnes CO2e.
        credit_standard: Certification standard (e.g. VCS, Gold Standard).
        documentation_text: Full project documentation pasted as text.
    """

    name: str = Field(min_length=1, max_length=256, description="Project name")
    description: str = Field(
        min_length=10, max_length=5000, description="Detailed project description"
    )
    project_type: ProjectType
    country: str = Field(min_length=1, max_length=128)
    vintage_year: int = Field(ge=2000, le=2035)
    estimated_credits: int = Field(ge=0, description="Estimated annual credits in tonnes CO2e")
    credit_standard: str = Field(
        min_length=1, max_length=128, description="e.g. VCS, Gold Standard"
    )
    documentation_text: str = Field(
        min_length=50,
        max_length=100000,
        description="Full project documentation text for AI verification",
    )
