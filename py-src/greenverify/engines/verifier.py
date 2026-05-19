"""
Carbon credit verification engine.

Orchestrates the full verification pipeline: project creation, LLM-based
analysis via Qwen, result parsing, and verification result persistence.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from ..models.carbon import (
    CarbonProject,
    ProjectStatus,
    RiskLevel,
    VerificationFormData,
    VerificationResult,
)
from ..services.market_data import GreenMarketDataService
from ..services.qwen_client import QwenClient

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Orchestration engine for carbon credit verification workflows.

    Coordinates the full pipeline from form submission through AI analysis
    to final verification result. Integrates with the Qwen LLM client for
    AI-powered assessment and the market data service for persistence.

    Attributes:
        _qwen_client: Async client for the Qwen LLM.
        _market_data: Service for accessing and persisting demo data.
    """

    def __init__(
        self,
        qwen_client: QwenClient | None = None,
        market_data: GreenMarketDataService | None = None,
    ) -> None:
        """Initialise the verification engine.

        Args:
            qwen_client: An optional pre-configured QwenClient instance. If not
                         provided, a new one will be created from environment
                         variables.
            market_data: An optional pre-configured GreenMarketDataService. If
                         not provided, a new default instance will be created.
        """
        self._qwen_client: QwenClient = qwen_client or QwenClient()
        self._market_data: GreenMarketDataService = market_data or GreenMarketDataService()
        logger.info("VerificationEngine initialised")

    async def submit_verification(
        self,
        form_data: VerificationFormData,
    ) -> VerificationResult:
        """Submit a new carbon project for AI-powered verification.

        Executes the full verification pipeline:
        1. Creates a CarbonProject from the form data.
        2. Calls the Qwen LLM to analyse the project documentation.
        3. Parses and validates the LLM's structured response.
        4. Persists the project and verification result.
        5. Returns the final VerificationResult.

        Args:
            form_data: The submitted verification form containing project
                       details and documentation text.

        Returns:
            A VerificationResult with the AI's assessment, score, risk
            classification, and recommendations.

        Raises:
            RuntimeError: If the LLM analysis or result parsing fails.
            ValueError: If the form data is invalid.
        """
        request_id = uuid.uuid4().hex
        logger.info(
            "Starting verification — request_id=%s, project=%s, type=%s",
            request_id,
            form_data.name,
            form_data.project_type,
        )

        # Step 1: Create the CarbonProject
        project = CarbonProject(
            project_id=uuid.uuid4().hex,
            name=form_data.name,
            description=form_data.description,
            project_type=form_data.project_type,
            country=form_data.country,
            vintage_year=form_data.vintage_year,
            estimated_annual_credits=form_data.estimated_credits,
            credit_standard=form_data.credit_standard,
            status=ProjectStatus.VERIFYING,
        )

        # Step 2: Call Qwen for verification analysis
        logger.info("Calling Qwen LLM for verification analysis — project_id=%s", project.project_id)
        llm_result = await self._qwen_client.verify_carbon_project(
            documentation=form_data.documentation_text,
            project_type=form_data.project_type.value,
            country=form_data.country,
        )

        # Step 3: Parse and validate the result
        verification_result = self._build_verification_result(
            request_id=request_id,
            project_id=project.project_id,
            llm_result=llm_result,
        )

        # Step 4: Update project status based on verification outcome
        if verification_result.pass_fail:
            project.status = ProjectStatus.VERIFIED
            project.verified_at = verification_result.verified_at
        else:
            project.status = ProjectStatus.REJECTED
            project.verified_at = verification_result.verified_at

        # Step 5: Persist
        self._market_data.add_project(project)
        self._market_data.add_verification(verification_result)

        logger.info(
            "Verification complete — project_id=%s, score=%d, pass=%s",
            project.project_id,
            verification_result.score,
            verification_result.pass_fail,
        )

        return verification_result

    @staticmethod
    def _build_verification_result(
        request_id: str,
        project_id: str,
        llm_result: dict,
    ) -> VerificationResult:
        """Transform the raw LLM output into a validated VerificationResult.

        Args:
            request_id: The verification request identifier.
            project_id: The carbon project identifier.
            llm_result: The parsed dictionary from the Qwen LLM.

        Returns:
            A fully populated VerificationResult instance.

        Raises:
            ValueError: If the LLM result contains invalid risk_level.
        """
        # Parse and validate risk_level
        raw_risk = llm_result.get("risk_level", "Medium")
        try:
            risk_level = RiskLevel(raw_risk)
        except ValueError:
            logger.warning(
                "Invalid risk_level from LLM: %s, defaulting to Medium",
                raw_risk,
            )
            risk_level = RiskLevel.MEDIUM

        return VerificationResult(
            request_id=request_id,
            project_id=project_id,
            score=llm_result["score"],
            risk_level=risk_level,
            assessment=llm_result["assessment"],
            recommendations=llm_result.get("recommendations", []),
            credit_amount_recommended=llm_result.get(
                "credit_amount_recommended",
                llm_result.get("recommended_credit_amount", 0),
            ),
            pass_fail=llm_result["pass_fail"],
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def include_verify_prompt() -> str:
        """Return the system prompt used for carbon credit verification.

        This method is exposed for reference, testing, and documentation
        purposes. The actual prompt is used internally by the QwenClient.

        Returns:
            The system prompt string that instructs Qwen to act as a
            carbon credit verification expert.
        """
        return (
            "You are an expert carbon credit verification analyst working for GreenVerify AI. "
            "You have deep expertise in carbon markets, greenhouse gas accounting methodologies "
            "(IPCC, GHG Protocol), carbon credit standards (VCS, Gold Standard, CDM, American "
            "Carbon Registry, Climate Action Reserve), and environmental science. Your role is "
            "to rigorously analyse carbon credit project documentation and provide comprehensive "
            "verification assessments covering additionality, permanence, measurability, leakage, "
            "methodology appropriateness, documentation quality, and regulatory compliance."
        )
