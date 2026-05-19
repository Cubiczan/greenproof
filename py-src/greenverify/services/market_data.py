"""
GreenVerify AI market data service.

Provides in-memory demo data for carbon credit projects, credit NFTs,
marketplace listings, and dashboard overview statistics. Designed for
development, testing, and demonstration purposes.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from ..models.carbon import (
    CarbonProject,
    CreditNFT,
    DashboardOverview,
    ListingStatus,
    MarketplaceListing,
    ProjectStatus,
    ProjectType,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class GreenMarketDataService:
    """In-memory data service for GreenVerify AI demo data.

    Manages collections of carbon credit projects, credit NFTs, marketplace
    listings, and verification results. Provides query methods for each
    entity type and dashboard aggregation.

    Attributes:
        _projects: Registry of carbon credit projects keyed by project_id.
        _credits: Registry of credit NFTs keyed by token_id.
        _listings: Registry of marketplace listings keyed by listing_id.
        _verifications: Registry of verification results keyed by request_id.
    """

    def __init__(self) -> None:
        """Initialise the service and seed demo data."""
        self._projects: dict[str, CarbonProject] = {}
        self._credits: dict[str, CreditNFT] = {}
        self._listings: dict[str, MarketplaceListing] = {}
        self._verifications: dict[str, VerificationResult] = {}
        self._seed_demo_data()
        logger.info(
            "GreenMarketDataService initialised — projects=%d, credits=%d, listings=%d",
            len(self._projects),
            len(self._credits),
            len(self._listings),
        )

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def get_all_projects(self) -> list[CarbonProject]:
        """Return all registered carbon credit projects.

        Returns:
            A list of all CarbonProject instances in the registry.
        """
        return list(self._projects.values())

    def get_project(self, project_id: str) -> CarbonProject | None:
        """Retrieve a single project by its identifier.

        Args:
            project_id: The unique project identifier.

        Returns:
            The matching CarbonProject, or None if not found.
        """
        return self._projects.get(project_id)

    def get_credits(self) -> list[CreditNFT]:
        """Return all minted credit NFTs.

        Returns:
            A list of all CreditNFT instances.
        """
        return list(self._credits.values())

    def get_credit(self, token_id: str) -> CreditNFT | None:
        """Retrieve a single credit NFT by token ID.

        Args:
            token_id: The on-chain token identifier.

        Returns:
            The matching CreditNFT, or None if not found.
        """
        return self._credits.get(token_id)

    def get_listings(self) -> list[MarketplaceListing]:
        """Return all marketplace listings.

        Returns:
            A list of all MarketplaceListing instances.
        """
        return list(self._listings.values())

    def get_listing(self, listing_id: str) -> MarketplaceListing | None:
        """Retrieve a single marketplace listing by its identifier.

        Args:
            listing_id: The unique listing identifier.

        Returns:
            The matching MarketplaceListing, or None if not found.
        """
        return self._listings.get(listing_id)

    def add_listing(self, token_id: str, price: float) -> MarketplaceListing | None:
        """Create a new marketplace listing for a credit NFT.

        Args:
            token_id: The credit NFT to list.
            price: Listing price in POT tokens.

        Returns:
            The created MarketplaceListing, or None if the token is not found.
        """
        credit = self._credits.get(token_id)
        if credit is None:
            return None

        listing = MarketplaceListing(
            token_id=token_id,
            seller=credit.owner,
            price=price,
        )
        self._listings[listing.listing_id] = listing
        return listing

    def buy_listing(self, listing_id: str) -> MarketplaceListing | CreditNFT | None:
        """Execute a purchase of an active marketplace listing.

        Transfers the credit NFT ownership to a demo buyer address and
        marks the listing as sold.

        Args:
            listing_id: The listing to purchase.

        Returns:
            A tuple of (listing, credit_nft) if successful, None otherwise.
        """
        listing = self._listings.get(listing_id)
        if listing is None or listing.status != ListingStatus.ACTIVE:
            return None

        credit = self._credits.get(listing.token_id)
        if credit is None:
            return None

        # Mark listing as sold and transfer ownership
        listing.status = ListingStatus.SOLD
        credit.owner = "0xBuyerDemo" + uuid.uuid4().hex[:10]

        return listing

    def add_project(self, project: CarbonProject) -> CarbonProject:
        """Register a new carbon credit project.

        Args:
            project: The CarbonProject to add.

        Returns:
            The added CarbonProject.
        """
        self._projects[project.project_id] = project
        return project

    def add_verification(self, result: VerificationResult) -> VerificationResult:
        """Record a verification result.

        Args:
            result: The VerificationResult to store.

        Returns:
            The stored VerificationResult.
        """
        self._verifications[result.request_id] = result
        return result

    def get_dashboard_overview(self) -> DashboardOverview:
        """Compute aggregated dashboard statistics.

        Returns:
            A DashboardOverview with platform-wide metrics.
        """
        total_credits = sum(c.amount for c in self._credits.values())
        traded_credits = sum(
            c.amount
            for c in self._credits.values()
            if c.owner.startswith("0xBuyer")
        )
        active = sum(
            1 for l in self._listings.values() if l.status == ListingStatus.ACTIVE
        )

        scores = [
            v.score for v in self._verifications.values()
        ]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Build recent verifications summary (last 5)
        recent = sorted(
            self._verifications.values(),
            key=lambda v: v.verified_at,
            reverse=True,
        )[:5]
        recent_summary: list[dict[str, Any]] = [
            {
                "request_id": v.request_id,
                "project_id": v.project_id,
                "score": v.score,
                "risk_level": v.risk_level.value if hasattr(v.risk_level, "value") else v.risk_level,
                "pass_fail": v.pass_fail,
                "verified_at": v.verified_at,
            }
            for v in recent
        ]

        return DashboardOverview(
            total_credits_verified=total_credits,
            total_credits_traded=traded_credits,
            total_projects=len(self._projects),
            active_listings=active,
            avg_verification_score=round(avg_score, 1),
            recent_verifications=recent_summary,
        )

    # ------------------------------------------------------------------
    # Demo data seeding
    # ------------------------------------------------------------------

    def _seed_demo_data(self) -> None:
        """Seed the service with realistic demo data for development.

        Creates 22 carbon credit projects spanning 4 project types across
        14 countries, 5 verified projects with minted credit NFTs, 3 active
        marketplace listings, and associated verification results.
        """
        now = datetime.now(timezone.utc).isoformat()

        # --- Projects ---
        project_data: list[dict[str, Any]] = [
            # Verified projects (5)
            {
                "project_id": "proj_001",
                "name": "Amazon Rainforest Reforestation Initiative",
                "description": (
                    "Large-scale reforestation of degraded Amazon rainforest areas in Pará state, "
                    "planting native species including Brazil nut, Jacaranda, and Ipê. The project "
                    "covers 12,000 hectares and has planted over 2.4 million trees since 2019, "
                    "with third-party monitoring by SGS and annual MRV reports."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Brazil",
                "vintage_year": 2023,
                "estimated_annual_credits": 45000,
                "credit_standard": "VCS",
                "documentation_urls": [
                    "https://example.com/docs/amazon-reforest-pdd.pdf",
                    "https://example.com/docs/amazon-reforest-mrv-2023.pdf",
                ],
                "status": ProjectStatus.VERIFIED,
                "submitted_at": "2023-06-15T10:00:00Z",
                "verified_at": "2023-08-20T14:30:00Z",
            },
            {
                "project_id": "proj_002",
                "name": "Rajasthan Solar Park Expansion",
                "description": (
                    "500 MW solar photovoltaic installation across 2,500 acres in Jodhpur district, "
                    "Rajasthan. Replaces coal-based grid electricity with clean solar power, "
                    "generating approximately 850 GWh annually. Monitored via IEC 61400-12 "
                    "standards with quarterly performance audits."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "India",
                "vintage_year": 2023,
                "estimated_annual_credits": 38000,
                "credit_standard": "Gold Standard",
                "documentation_urls": [
                    "https://example.com/docs/rajasthan-solar-pdd.pdf",
                ],
                "status": ProjectStatus.VERIFIED,
                "submitted_at": "2023-03-10T08:00:00Z",
                "verified_at": "2023-05-18T12:00:00Z",
            },
            {
                "project_id": "proj_003",
                "name": "Inner Mongolia Wind Farm Cluster",
                "description": (
                    "Grid-connected wind energy project with 200 turbines (total 600 MW capacity) "
                    "in the Inner Mongolia Autonomous Region. The project displaces electricity "
                    "from predominantly coal-fired power plants in the North China Power Grid. "
                    "Annual generation averages 1,400 GWh."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "China",
                "vintage_year": 2023,
                "estimated_annual_credits": 52000,
                "credit_standard": "VCS",
                "documentation_urls": [
                    "https://example.com/docs/inner-mongolia-wind-pdd.pdf",
                ],
                "status": ProjectStatus.VERIFIED,
                "submitted_at": "2023-01-22T09:00:00Z",
                "verified_at": "2023-04-05T16:00:00Z",
            },
            {
                "project_id": "proj_004",
                "name": "Oklahoma Landfill Methane Capture",
                "description": (
                    "Methane capture and flaring system at the Oklahoma City Municipal Landfill, "
                    "processing 4,200 m³/hour of landfill gas. The project destroys methane "
                    "(GWP-25) that would otherwise vent to atmosphere, and also generates 8 MW "
                    "of electricity from an on-site gas engine."
                ),
                "project_type": ProjectType.METHANE_CAPTURE,
                "country": "United States",
                "vintage_year": 2022,
                "estimated_annual_credits": 28000,
                "credit_standard": "American Carbon Registry",
                "documentation_urls": [
                    "https://example.com/docs/oklahoma-methane-pdd.pdf",
                ],
                "status": ProjectStatus.VERIFIED,
                "submitted_at": "2022-09-01T11:00:00Z",
                "verified_at": "2022-12-15T10:00:00Z",
            },
            {
                "project_id": "proj_005",
                "name": "Congo Basin Mangrove Restoration",
                "description": (
                    "Community-led mangrove restoration along 180 km of coastline in the Republic "
                    "of Congo. The project has restored 3,500 hectares of degraded mangrove "
                    "ecosystems, providing coastal protection, biodiversity habitat, and carbon "
                    "sequestration. Verified by Bureau Veritas."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Republic of Congo",
                "vintage_year": 2023,
                "estimated_annual_credits": 18000,
                "credit_standard": "VCS + CCB",
                "documentation_urls": [
                    "https://example.com/docs/congo-mangrove-pdd.pdf",
                ],
                "status": ProjectStatus.VERIFIED,
                "submitted_at": "2023-04-20T13:00:00Z",
                "verified_at": "2023-07-10T09:00:00Z",
            },
            # Pending / Verifying projects
            {
                "project_id": "proj_006",
                "name": "Kenya Great Rift Valley Geothermal",
                "description": (
                    "Geothermal energy extraction project near Lake Naivasha in the Kenyan Rift "
                    "Valley. Three production wells with a combined capacity of 75 MW feeding into "
                    "the national grid, displacing diesel peaking plants."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "Kenya",
                "vintage_year": 2024,
                "estimated_annual_credits": 15000,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_007",
                "name": "Northern Vietnam Agroforestry Program",
                "description": (
                    "Smallholder agroforestry initiative in Lào Cai and Điện Biên provinces "
                    "integrating fruit trees (longan, lychee) with nitrogen-fixing leguminous "
                    "species. Covers 8,000 hectares across 4,200 farming households."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Vietnam",
                "vintage_year": 2024,
                "estimated_annual_credits": 12000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_008",
                "name": "Punjab Rice Paddy Methane Reduction",
                "description": (
                    "Implementation of alternate wetting and drying (AWD) irrigation technique "
                    "across 25,000 hectares of rice paddies in Punjab, India. Reduces methane "
                    "emissions from anaerobic decomposition in flooded rice fields by 30-50%."
                ),
                "project_type": ProjectType.METHANE_CAPTURE,
                "country": "India",
                "vintage_year": 2024,
                "estimated_annual_credits": 22000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.VERIFYING,
                "submitted_at": "2024-01-10T07:00:00Z",
            },
            {
                "project_id": "proj_009",
                "name": "Chile Andean Hydropower Rehabilitation",
                "description": (
                    "Rehabilitation and modernisation of three small-scale run-of-river hydro "
                    "plants in the Los Lagos Region of Chile. Combined capacity of 45 MW "
                    "displacing fossil fuel power in the Chilean grid."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "Chile",
                "vintage_year": 2024,
                "estimated_annual_credits": 8500,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_010",
                "name": "Germany Industrial Waste Heat Recovery",
                "description": (
                    "Installation of organic Rankine cycle (ORC) waste heat recovery systems at "
                    "three steel manufacturing plants in North Rhine-Westphalia. Captures low-grade "
                    "waste heat and converts it to electricity, reducing natural gas consumption."
                ),
                "project_type": ProjectType.INDUSTRIAL,
                "country": "Germany",
                "vintage_year": 2024,
                "estimated_annual_credits": 11000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_011",
                "name": "Morocco Concentrated Solar Power Plant",
                "description": (
                    "150 MW parabolic trough concentrated solar power (CSP) plant near Ouarzazate, "
                    "Morocco with 5-hour thermal storage. Provides reliable clean energy dispatch "
                    "aligned with peak demand periods."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "Morocco",
                "vintage_year": 2023,
                "estimated_annual_credits": 32000,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.VERIFYING,
                "submitted_at": "2024-02-05T14:00:00Z",
            },
            {
                "project_id": "proj_012",
                "name": "British Columbia Forest Conservation",
                "description": (
                    "Improved forest management project on 95,000 hectares of boreal forest in "
                    "British Columbia, Canada. Prevents planned logging of old-growth stands and "
                    "implements sustainable timber harvesting practices."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Canada",
                "vintage_year": 2024,
                "estimated_annual_credits": 42000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_013",
                "name": "Australia Livestock Methane Capture",
                "description": (
                    "Covered anaerobic digester systems at 12 large-scale cattle feedlots across "
                    "Queensland and New South Wales. Captures biogas from manure, converts methane "
                    "to CO2 through combustion, and generates renewable biogas energy."
                ),
                "project_type": ProjectType.METHANE_CAPTURE,
                "country": "Australia",
                "vintage_year": 2024,
                "estimated_annual_credits": 16000,
                "credit_standard": "Australian Carbon Credit Unit",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_014",
                "name": "Nigeria Cassava Biogas Programme",
                "description": (
                    "Community-scale biogas plants processing cassava processing waste across "
                    "15 facilities in Oyo and Osun states. Reduces open burning of agricultural "
                    "waste and provides clean cooking fuel to local communities."
                ),
                "project_type": ProjectType.METHANE_CAPTURE,
                "country": "Nigeria",
                "vintage_year": 2024,
                "estimated_annual_credits": 7500,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_015",
                "name": "Colombian Coffee Agroforestry",
                "description": (
                    "Shade-grown coffee agroforestry system integrating native Inga and Guamo "
                    "trees with coffee production in Antioquia and Huila departments. 15,000 "
                    "hectares managed by 6,500 smallholder farming families."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Colombia",
                "vintage_year": 2024,
                "estimated_annual_credits": 20000,
                "credit_standard": "VCS + CCB",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_016",
                "name": "Bangladesh Rooftop Solar Programme",
                "description": (
                    "Distributed rooftop solar PV installations across 500 commercial and industrial "
                    "buildings in Dhaka and Chittagong. Total installed capacity of 80 MW, reducing "
                    "reliance on gas-fired grid electricity during peak hours."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "Bangladesh",
                "vintage_year": 2024,
                "estimated_annual_credits": 9000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_017",
                "name": "Japan Industrial CCS Pilot",
                "description": (
                    "Carbon capture and storage pilot at a petrochemical complex in Kawasaki, Japan. "
                    "Captures 400,000 tonnes CO2 annually from hydrogen production and flue gas, "
                    "with geological storage in depleted offshore gas reservoirs."
                ),
                "project_type": ProjectType.INDUSTRIAL,
                "country": "Japan",
                "vintage_year": 2024,
                "estimated_annual_credits": 400000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_018",
                "name": "Indonesia Peatland Rewetting",
                "description": (
                    "Large-scale peatland rewetting and conservation project in Central Kalimantan, "
                    "Indonesia. Restores hydrology across 20,000 hectares of degraded tropical "
                    "peatland, preventing oxidation and fire-related emissions."
                ),
                "project_type": ProjectType.REFORESTATION,
                "country": "Indonesia",
                "vintage_year": 2024,
                "estimated_annual_credits": 35000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_019",
                "name": "South Korea Offshore Wind Farm",
                "description": (
                    "Offshore wind energy project with 50 turbines (300 MW total) in the waters "
                    "off Ulsan, South Korea. Provides clean electricity to the Korean national grid, "
                    "displacing coal and LNG generation."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "South Korea",
                "vintage_year": 2024,
                "estimated_annual_credits": 25000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.VERIFYING,
                "submitted_at": "2024-01-28T11:00:00Z",
            },
            {
                "project_id": "proj_020",
                "name": "Tanzania Charcoal Alternative Stoves",
                "description": (
                    "Distribution of 200,000 improved cookstoves using ethanol fuel to households "
                    "in Dar es Salaam and surrounding regions. Reduces charcoal consumption and "
                    "associated deforestation pressure."
                ),
                "project_type": ProjectType.INDUSTRIAL,
                "country": "Tanzania",
                "vintage_year": 2024,
                "estimated_annual_credits": 6000,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_021",
                "name": "Ethiopia Clean Biomass Energy",
                "description": (
                    "Sustainable biomass briquette production from agricultural residues in the "
                    "Amhara region. Replaces traditional charcoal with carbon-neutral briquettes, "
                    "serving 80,000 households in Bahir Dar and Gondar."
                ),
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "Ethiopia",
                "vintage_year": 2024,
                "estimated_annual_credits": 5000,
                "credit_standard": "Gold Standard",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
            {
                "project_id": "proj_022",
                "name": "Poland Industrial Efficiency Upgrade",
                "description": (
                    "Energy efficiency upgrades at 8 cement manufacturing plants across Poland, "
                    "including clinker substitution, waste heat recovery, and variable-speed "
                    "drives. Reduces specific energy consumption by 18%."
                ),
                "project_type": ProjectType.INDUSTRIAL,
                "country": "Poland",
                "vintage_year": 2024,
                "estimated_annual_credits": 14000,
                "credit_standard": "VCS",
                "documentation_urls": [],
                "status": ProjectStatus.PENDING,
                "submitted_at": now,
            },
        ]

        for pd in project_data:
            project = CarbonProject(**pd)
            self._projects[project.project_id] = project

        # --- Credit NFTs (5 minted for verified projects) ---
        credit_data: list[dict[str, Any]] = [
            {
                "token_id": "nft_001",
                "project_id": "proj_001",
                "owner": "0xSellerA1b2c3d4e5",
                "amount": 45000,
                "vintage_year": 2023,
                "credit_standard": "VCS",
                "project_name": "Amazon Rainforest Reforestation Initiative",
                "project_type": ProjectType.REFORESTATION,
                "country": "Brazil",
                "minted_at": "2023-08-21T10:00:00Z",
                "onchain_tx_hash": "0xabc123def456789abc123def456789abc123def456789abc123def456789abcd",
            },
            {
                "token_id": "nft_002",
                "project_id": "proj_002",
                "owner": "0xSellerB6f7g8h9i0",
                "amount": 38000,
                "vintage_year": 2023,
                "credit_standard": "Gold Standard",
                "project_name": "Rajasthan Solar Park Expansion",
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "India",
                "minted_at": "2023-05-19T08:00:00Z",
                "onchain_tx_hash": "0xdef789abc123456def789abc123456def789abc123456def789abc123456def7",
            },
            {
                "token_id": "nft_003",
                "project_id": "proj_003",
                "owner": "0xSellerC1a2b3c4d5",
                "amount": 52000,
                "vintage_year": 2023,
                "credit_standard": "VCS",
                "project_name": "Inner Mongolia Wind Farm Cluster",
                "project_type": ProjectType.RENEWABLE_ENERGY,
                "country": "China",
                "minted_at": "2023-04-06T12:00:00Z",
                "onchain_tx_hash": "0x456abc789def012456abc789def012456abc789def012456abc789def012456ab",
            },
            {
                "token_id": "nft_004",
                "project_id": "proj_004",
                "owner": "0xSellerD9e8f7g6h5",
                "amount": 28000,
                "vintage_year": 2022,
                "credit_standard": "American Carbon Registry",
                "project_name": "Oklahoma Landfill Methane Capture",
                "project_type": ProjectType.METHANE_CAPTURE,
                "country": "United States",
                "minted_at": "2022-12-16T09:00:00Z",
                "onchain_tx_hash": "0x789def012abc345789def012abc345789def012abc345789def012abc345789d",
            },
            {
                "token_id": "nft_005",
                "project_id": "proj_005",
                "owner": "0xSellerE4d3c2b1a0",
                "amount": 18000,
                "vintage_year": 2023,
                "credit_standard": "VCS + CCB",
                "project_name": "Congo Basin Mangrove Restoration",
                "project_type": ProjectType.REFORESTATION,
                "country": "Republic of Congo",
                "minted_at": "2023-07-11T11:00:00Z",
                "onchain_tx_hash": "0x012abc345def678012abc345def678012abc345def678012abc345def678012a",
            },
        ]

        for cd in credit_data:
            credit = CreditNFT(**cd)
            self._credits[credit.token_id] = credit

        # --- Marketplace Listings (3 active) ---
        listing_data: list[dict[str, Any]] = [
            {
                "listing_id": "list_001",
                "token_id": "nft_001",
                "seller": "0xSellerA1b2c3d4e5",
                "price": 2450.0,
                "listed_at": "2024-01-15T08:00:00Z",
                "status": ListingStatus.ACTIVE,
            },
            {
                "listing_id": "list_002",
                "token_id": "nft_002",
                "seller": "0xSellerB6f7g8h9i0",
                "price": 1890.0,
                "listed_at": "2024-02-01T10:00:00Z",
                "status": ListingStatus.ACTIVE,
            },
            {
                "listing_id": "list_003",
                "token_id": "nft_004",
                "seller": "0xSellerD9e8f7g6h5",
                "price": 1540.0,
                "listed_at": "2024-02-10T12:00:00Z",
                "status": ListingStatus.ACTIVE,
            },
        ]

        for ld in listing_data:
            listing = MarketplaceListing(**ld)
            self._listings[listing.listing_id] = listing

        # --- Verification Results for verified projects ---
        verification_data: list[dict[str, Any]] = [
            {
                "request_id": "req_001",
                "project_id": "proj_001",
                "score": 87,
                "risk_level": "Low",
                "assessment": (
                    "The Amazon Rainforest Reforestation Initiative demonstrates strong "
                    "additionality through its focus on degraded lands that would not "
                    "naturally regenerate within the project timeframe. The use of native "
                    "species and comprehensive MRV framework with SGS third-party "
                    "monitoring provides high confidence in permanence and measurability. "
                    "Leakage risk is minimal due to the project's buffer zone design and "
                    "community engagement programmes that prevent displacement of "
                    "agricultural activity."
                ),
                "recommendations": [
                    "Expand the buffer zone monitoring to include satellite-based NDVI analysis",
                    "Consider obtaining CCB (Climate, Community & Biodiversity) certification",
                    "Publish annual biodiversity impact assessments",
                ],
                "credit_amount_recommended": 42000,
                "pass_fail": True,
                "verified_at": "2023-08-20T14:30:00Z",
            },
            {
                "request_id": "req_002",
                "project_id": "proj_002",
                "score": 92,
                "risk_level": "Low",
                "assessment": (
                    "The Rajasthan Solar Park Expansion is a highly credible renewable "
                    "energy project. Additionality is clearly established as the project "
                    "replaces new coal capacity that was planned for the same grid "
                    "connection point. The Gold Standard certification process includes "
                    "stringent stakeholder consultation and sustainable development "
                    "contribution requirements, both of which are well-documented."
                ),
                "recommendations": [
                    "Consider adding battery storage to improve grid stability contribution",
                    "Document local employment creation numbers for impact reporting",
                ],
                "credit_amount_recommended": 36000,
                "pass_fail": True,
                "verified_at": "2023-05-18T12:00:00Z",
            },
            {
                "request_id": "req_003",
                "project_id": "proj_003",
                "score": 84,
                "risk_level": "Low",
                "assessment": (
                    "The Inner Mongolia Wind Farm Cluster is a substantial renewable "
                    "energy project with clear additionality in a grid dominated by "
                    "coal-fired generation. The project's 600 MW capacity provides "
                    "significant displacement of fossil fuel electricity. Monitoring "
                    "follows IEC standards and baseline methodology is conservative."
                ),
                "recommendations": [
                    "Strengthen community benefit-sharing mechanisms",
                    "Add avian and bat monitoring protocols",
                    "Consider decommissioning plan for end-of-life turbines",
                ],
                "credit_amount_recommended": 49000,
                "pass_fail": True,
                "verified_at": "2023-04-05T16:00:00Z",
            },
            {
                "request_id": "req_004",
                "project_id": "proj_004",
                "score": 78,
                "risk_level": "Medium",
                "assessment": (
                    "The Oklahoma Landfill Methane Capture project effectively addresses "
                    "methane emissions from a large municipal landfill. The project "
                    "combines gas collection with electricity generation, providing "
                    "additional environmental co-benefits. Risk level is Medium due to "
                    "potential for gas collection efficiency to decline over time as "
                    "the landfill reaches capacity and waste composition changes."
                ),
                "recommendations": [
                    "Implement enhanced gas collection efficiency monitoring",
                    "Develop contingency plan for declining gas yields in later years",
                    "Consider post-closure care funding mechanisms",
                ],
                "credit_amount_recommended": 24000,
                "pass_fail": True,
                "verified_at": "2022-12-15T10:00:00Z",
            },
            {
                "request_id": "req_005",
                "project_id": "proj_005",
                "score": 81,
                "risk_level": "Low",
                "assessment": (
                    "The Congo Basin Mangrove Restoration project is a well-designed "
                    "blue carbon initiative with strong community involvement and "
                    "biodiversity co-benefits. Mangrove ecosystems provide excellent "
                    "permanence when properly managed, and the project's CCB "
                    "certification provides additional assurance on social and "
                    "environmental safeguards."
                ),
                "recommendations": [
                    "Establish long-term monitoring plots with permanent markers",
                    "Develop contingency plans for extreme weather events",
                    "Engage additional local communities in the project zone",
                ],
                "credit_amount_recommended": 16000,
                "pass_fail": True,
                "verified_at": "2023-07-10T09:00:00Z",
            },
        ]

        for vd in verification_data:
            result = VerificationResult(**vd)
            self._verifications[result.request_id] = result
