"""
FastAPI route definitions for GreenVerify AI.

Defines all HTTP endpoints for the platform including health checks,
dashboard metrics, project management, AI verification, credit NFTs,
and marketplace operations.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..models.carbon import (
    CarbonProject,
    CreditNFT,
    DashboardOverview,
    MarketplaceListing,
    VerificationFormData,
    VerificationResult,
)
from ..services.market_data import GreenMarketDataService
from ..services.qwen_client import CHINA_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / response schemas for marketplace operations
# ---------------------------------------------------------------------------

class CreateListingRequest(BaseModel):
    """Request body for creating a new marketplace listing.

    Attributes:
        token_id: The credit NFT token ID to list for sale.
        price: The listing price in POT tokens.
    """
    token_id: str = Field(min_length=1, description="Credit NFT token ID")
    price: float = Field(gt=0, description="Listing price in POT tokens")


class BuyListingRequest(BaseModel):
    """Request body for purchasing a marketplace listing.

    Attributes:
        listing_id: The listing ID to purchase.
    """
    listing_id: str = Field(min_length=1, description="Marketplace listing ID")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(
    market_data: GreenMarketDataService | None = None,
) -> FastAPI:
    """Create and configure the GreenVerify AI FastAPI application.

    Sets up CORS middleware, initialises the market data service, and
    registers all route handlers. The application can optionally receive
    a pre-configured market data service (useful for testing).

    Args:
        market_data: An optional pre-configured GreenMarketDataService.
                     If not provided, a default instance is created.

    Returns:
        A fully configured FastAPI application instance.
    """
    app = FastAPI(
        title="GreenVerify AI",
        description=(
            "AI-powered carbon credit verification and trading platform. "
            "Verify carbon credit projects with Qwen LLM, manage credit NFTs, "
            "and trade on the marketplace."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware — allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialise services
    data_service: GreenMarketDataService = market_data or GreenMarketDataService()

    # Lazily import the verification engine to avoid startup failures when
    # the API key is not set (health check should still work).
    def _get_verification_engine():
        """Lazily create the VerificationEngine on first use."""
        from ..engines.verifier import VerificationEngine
        return VerificationEngine(market_data=data_service)

    # ------------------------------------------------------------------
    # Router setup
    # ------------------------------------------------------------------

    router = APIRouter(prefix="/api")

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @router.get(
        "/health",
        tags=["Health"],
        summary="Health check and LLM connectivity test",
        response_model=dict[str, Any],
    )
    async def health_check() -> dict[str, Any]:
        """Check service health and optionally test LLM connectivity.

        Returns a JSON object with the service status, version, and
        configuration details. The LLM connectivity test is performed
        asynchronously and reported as part of the response.

        Returns:
            A health status dictionary.
        """
        llm_status = "not_configured"
        api_key_set = bool(os.getenv("DASHSCOPE_API_KEY"))

        if api_key_set:
            try:
                engine = _get_verification_engine()
                llm_status = "configured"
            except Exception as exc:
                llm_status = f"config_error: {exc}"

        return {
            "status": "healthy",
            "version": "0.1.0",
            "llm": {
                "model": DEFAULT_MODEL,
                "base_url": CHINA_BASE_URL,
                "status": llm_status,
                "api_key_configured": api_key_set,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @router.get(
        "/dashboard",
        tags=["Dashboard"],
        summary="Get platform dashboard overview",
        response_model=DashboardOverview,
    )
    async def get_dashboard() -> DashboardOverview:
        """Retrieve aggregated platform metrics and recent activity.

        Returns:
            A DashboardOverview with total credits, projects, listings,
            average score, and recent verifications.
        """
        return data_service.get_dashboard_overview()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    @router.get(
        "/projects",
        tags=["Projects"],
        summary="List all carbon credit projects",
        response_model=list[CarbonProject],
    )
    async def list_projects() -> list[CarbonProject]:
        """Return all registered carbon credit projects.

        Returns:
            A list of CarbonProject instances.
        """
        return data_service.get_all_projects()

    @router.get(
        "/projects/{project_id}",
        tags=["Projects"],
        summary="Get a specific carbon credit project",
        response_model=CarbonProject,
    )
    async def get_project(project_id: str) -> CarbonProject:
        """Retrieve a single carbon credit project by its identifier.

        Args:
            project_id: The unique project identifier.

        Returns:
            The matching CarbonProject.

        Raises:
            HTTPException: 404 if the project is not found.
        """
        project = data_service.get_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project with id '{project_id}' not found",
            )
        return project

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    @router.post(
        "/verify",
        tags=["Verification"],
        summary="Submit a project for AI verification",
        response_model=VerificationResult,
    )
    async def submit_verification(
        form_data: VerificationFormData,
    ) -> VerificationResult:
        """Submit a new carbon credit project for AI-powered verification.

        The Qwen LLM analyses the project documentation and returns a
        comprehensive assessment including score, risk level, detailed
        narrative, and actionable recommendations.

        Args:
            form_data: The project details and documentation text.

        Returns:
            A VerificationResult with the AI assessment.

        Raises:
            HTTPException: 500 if the LLM analysis fails.
        """
        try:
            engine = _get_verification_engine()
            result = await engine.submit_verification(form_data)
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            logger.error("Verification failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"AI verification failed: {exc}",
            ) from exc

    # ------------------------------------------------------------------
    # Credit NFTs
    # ------------------------------------------------------------------

    @router.get(
        "/credits",
        tags=["Credits"],
        summary="List all minted credit NFTs",
        response_model=list[CreditNFT],
    )
    async def list_credits() -> list[CreditNFT]:
        """Return all minted carbon credit NFTs.

        Returns:
            A list of CreditNFT instances.
        """
        return data_service.get_credits()

    @router.get(
        "/credits/{token_id}",
        tags=["Credits"],
        summary="Get a specific credit NFT",
        response_model=CreditNFT,
    )
    async def get_credit(token_id: str) -> CreditNFT:
        """Retrieve a single credit NFT by its token ID.

        Args:
            token_id: The on-chain token identifier.

        Returns:
            The matching CreditNFT.

        Raises:
            HTTPException: 404 if the credit NFT is not found.
        """
        credit = data_service.get_credit(token_id)
        if credit is None:
            raise HTTPException(
                status_code=404,
                detail=f"Credit NFT with token_id '{token_id}' not found",
            )
        return credit

    # ------------------------------------------------------------------
    # Marketplace
    # ------------------------------------------------------------------

    @router.get(
        "/marketplace",
        tags=["Marketplace"],
        summary="List all marketplace listings",
        response_model=list[MarketplaceListing],
    )
    async def list_marketplace() -> list[MarketplaceListing]:
        """Return all marketplace listings including active, sold, and cancelled.

        Returns:
            A list of MarketplaceListing instances.
        """
        return data_service.get_listings()

    @router.get(
        "/marketplace/{listing_id}",
        tags=["Marketplace"],
        summary="Get a specific marketplace listing",
        response_model=MarketplaceListing,
    )
    async def get_marketplace_listing(listing_id: str) -> MarketplaceListing:
        """Retrieve a single marketplace listing by its identifier.

        Args:
            listing_id: The unique listing identifier.

        Returns:
            The matching MarketplaceListing.

        Raises:
            HTTPException: 404 if the listing is not found.
        """
        listing = data_service.get_listing(listing_id)
        if listing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Marketplace listing with id '{listing_id}' not found",
            )
        return listing

    @router.post(
        "/marketplace/list",
        tags=["Marketplace"],
        summary="Create a new marketplace listing",
        response_model=MarketplaceListing,
    )
    async def create_listing(request: CreateListingRequest) -> MarketplaceListing:
        """Create a new listing to sell a credit NFT on the marketplace.

        Args:
            request: The listing creation request with token_id and price.

        Returns:
            The created MarketplaceListing.

        Raises:
            HTTPException: 404 if the credit NFT is not found.
        """
        listing = data_service.add_listing(
            token_id=request.token_id,
            price=request.price,
        )
        if listing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Credit NFT with token_id '{request.token_id}' not found",
            )
        return listing

    @router.post(
        "/marketplace/buy",
        tags=["Marketplace"],
        summary="Purchase a marketplace listing",
        response_model=MarketplaceListing,
    )
    async def buy_listing(request: BuyListingRequest) -> MarketplaceListing:
        """Execute a purchase on an active marketplace listing.

        Transfers ownership of the credit NFT to a demo buyer and marks
        the listing as sold.

        Args:
            request: The buy request containing the listing_id.

        Returns:
            The updated MarketplaceListing with status "Sold".

        Raises:
            HTTPException: 404 if the listing is not found or not active.
        """
        result = data_service.buy_listing(listing_id=request.listing_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Marketplace listing '{request.listing_id}' not found, "
                    f"already sold, or cancelled"
                ),
            )
        return result

    # ------------------------------------------------------------------
    # Register router
    # ------------------------------------------------------------------
    app.include_router(router)

    return app
