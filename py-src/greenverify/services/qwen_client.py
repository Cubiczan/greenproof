"""
Alibaba Cloud DashScope Qwen LLM client.

Provides an async interface to the Qwen-plus model via the OpenAI-compatible
DashScope API with automatic retry logic and China/Singapore endpoint fallback.

Environment variables:
    DASHSCOPE_API_KEY: API key for DashScope (required).
    DASHSCOPE_BASE_URL: Override the primary API base URL (optional).
    DASHSCOPE_MODEL: Model name override (default: qwen-plus).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# DashScope endpoint constants
CHINA_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
SINGAPORE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

DEFAULT_MODEL: str = "qwen-plus"
MAX_RETRIES: int = 3


class QwenClient:
    """Async client for Alibaba Cloud DashScope Qwen LLM.

    Wraps the OpenAI-compatible SDK to interact with Qwen-plus for carbon
    credit verification analysis. Includes automatic retry with endpoint
    fallback from the China region to the Singapore region.

    Attributes:
        model: The Qwen model identifier being used.
        _api_key: DashScope API key.
        _primary_url: Primary (China) endpoint URL.
        _fallback_url: Fallback (Singapore) endpoint URL.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialise the Qwen client with configuration from arguments or environment.

        Args:
            api_key: DashScope API key. Falls back to ``DASHSCOPE_API_KEY`` env var.
            base_url: Override the primary base URL. Falls back to ``DASHSCOPE_BASE_URL``
                      env var, then the China endpoint.
            model: Model name. Falls back to ``DASHSCOPE_MODEL`` env var, then ``qwen-plus``.

        Raises:
            ValueError: If no API key is available.
        """
        self._api_key: str = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "DashScope API key is required. Set DASHSCOPE_API_KEY environment variable "
                "or pass api_key to QwenClient constructor."
            )

        self.model: str = model or os.getenv("DASHSCOPE_MODEL", DEFAULT_MODEL)
        self._primary_url: str = base_url or os.getenv("DASHSCOPE_BASE_URL", CHINA_BASE_URL)
        self._fallback_url: str = SINGAPORE_BASE_URL

        logger.info(
            "QwenClient initialised — model=%s, primary_url=%s, fallback_url=%s",
            self.model,
            self._primary_url,
            self._fallback_url,
        )

    def _create_client(self, base_url: str) -> AsyncOpenAI:
        """Create an AsyncOpenAI client bound to the given base URL.

        Args:
            base_url: The DashScope-compatible endpoint URL.

        Returns:
            A configured AsyncOpenAI instance.
        """
        return AsyncOpenAI(
            api_key=self._api_key,
            base_url=base_url,
        )

    async def _chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Send a chat completion request to the Qwen model.

        Args:
            system_prompt: The system / instruction message.
            user_prompt: The user message containing the verification payload.

        Returns:
            The assistant's response content as a string.

        Raises:
            RuntimeError: If all retry attempts and endpoint fallbacks fail.
        """
        last_error: Exception | None = None
        endpoints = [self._primary_url, self._fallback_url]

        for endpoint_url in endpoints:
            client = self._create_client(endpoint_url)
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(
                        "Calling Qwen model — endpoint=%s, attempt=%d/%d",
                        endpoint_url,
                        attempt,
                        MAX_RETRIES,
                    )
                    response = await client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.2,
                        max_tokens=4096,
                        response_format={"type": "json_object"},
                    )
                    content = response.choices[0].message.content or ""
                    logger.info(
                        "Qwen response received — tokens=%s",
                        getattr(response.usage, "total_tokens", "N/A"),
                    )
                    return content

                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "Qwen call failed — endpoint=%s, attempt=%d/%d, error=%s",
                        endpoint_url,
                        attempt,
                        MAX_RETRIES,
                        exc,
                    )

            logger.warning(
                "All %d attempts failed for endpoint %s, trying fallback...",
                MAX_RETRIES,
                endpoint_url,
            )

        raise RuntimeError(
            f"Qwen LLM call failed after {MAX_RETRIES} retries across all endpoints. "
            f"Last error: {last_error}"
        )

    async def verify_carbon_project(
        self,
        documentation: str,
        project_type: str,
        country: str,
    ) -> dict[str, Any]:
        """Analyse carbon credit documentation using the Qwen LLM.

        Sends the project documentation along with a detailed verification prompt
        and returns a structured dictionary with the verification assessment.

        Args:
            documentation: The full text of the project documentation.
            project_type: The project category (e.g. "Reforestation").
            country: The country where the project is located.

        Returns:
            A dictionary containing:
                - ``score`` (int): Verification score 0-100.
                - ``risk_level`` (str): One of Low, Medium, High, Critical.
                - ``assessment`` (str): Detailed narrative assessment.
                - ``recommendations`` (list[str]): Actionable recommendations.
                - ``recommended_credit_amount`` (int): Verified credit tonnes CO2e.
                - ``pass_fail`` (bool): Whether the project passes verification.

        Raises:
            RuntimeError: If the LLM call fails or response parsing fails.
        """
        system_prompt = self._build_verification_system_prompt()
        user_prompt = self._build_verification_user_prompt(
            documentation=documentation,
            project_type=project_type,
            country=country,
        )

        raw_response: str = await self._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return self._parse_verification_response(raw_response)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_verification_system_prompt() -> str:
        """Return the system prompt for carbon credit verification.

        Returns:
            A detailed system prompt instructing Qwen to act as a carbon
            credit verification expert.
        """
        return (
            "You are an expert carbon credit verification analyst working for GreenVerify AI, "
            "a leading AI-powered carbon credit verification and trading platform. You have deep "
            "expertise in carbon markets, greenhouse gas accounting methodologies (IPCC, GHG "
            "Protocol), carbon credit standards (VCS, Gold Standard, CDM, American Carbon "
            "Registry, Climate Action Reserve), and environmental science.\n\n"
            "Your role is to rigorously analyse carbon credit project documentation and provide "
            "a comprehensive verification assessment. You must evaluate:\n"
            "1. **Additionality** — Would the emission reductions have occurred without this project?\n"
            "2. **Permanence** — Is the carbon sequestration or reduction permanent?\n"
            "3. **Measurability** — Can emission reductions be accurately measured and monitored?\n"
            "4. **Leakage** — Are there unintended increases in emissions elsewhere?\n"
            "5. **Verification methodology** — Is the methodology appropriate and correctly applied?\n"
            "6. **Documentation quality** — Is the supporting documentation thorough and credible?\n"
            "7. **Compliance** — Does the project comply with relevant standards and regulations?\n\n"
            "You MUST respond with a valid JSON object containing exactly these fields:\n"
            "- \"score\": integer from 0 to 100 representing overall verification confidence\n"
            "- \"risk_level\": one of \"Low\", \"Medium\", \"High\", \"Critical\"\n"
            "- \"assessment\": detailed narrative assessment (2-4 paragraphs)\n"
            "- \"recommendations\": array of 3-7 actionable improvement recommendations as strings\n"
            "- \"recommended_credit_amount\": integer representing verified credit amount in tonnes CO2e\n"
            "- \"pass_fail\": boolean indicating whether the project passes verification "
            "(generally pass if score >= 60 and risk_level is not Critical)\n\n"
            "Be thorough, objective, and evidence-based in your analysis. If documentation is "
            "insufficient, note this in your assessment and recommend specific improvements."
        )

    @staticmethod
    def _build_verification_user_prompt(
        documentation: str,
        project_type: str,
        country: str,
    ) -> str:
        """Return the user prompt containing the project data for verification.

        Args:
            documentation: The full project documentation text.
            project_type: The carbon project category.
            country: The project's country.

        Returns:
            A user prompt string for the LLM.
        """
        return (
            f"Please verify the following carbon credit project:\n\n"
            f"**Project Type:** {project_type}\n"
            f"**Country:** {country}\n\n"
            f"**Project Documentation:**\n{documentation}\n\n"
            f"Provide your verification assessment as a JSON object with the fields: "
            f"score, risk_level, assessment, recommendations, recommended_credit_amount, pass_fail."
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_verification_response(raw_response: str) -> dict[str, Any]:
        """Parse and validate the LLM's JSON response into a structured dict.

        Args:
            raw_response: Raw JSON string from the LLM.

        Returns:
            Validated dictionary with verification result fields.

        Raises:
            RuntimeError: If the response is not valid JSON or missing required fields.
        """
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse Qwen verification response as JSON: {exc}\n"
                f"Raw response: {raw_response[:500]}"
            ) from exc

        required_fields: list[str] = [
            "score",
            "risk_level",
            "assessment",
            "recommendations",
            "recommended_credit_amount",
            "pass_fail",
        ]

        missing = [f for f in required_fields if f not in data]
        if missing:
            raise RuntimeError(
                f"Qwen verification response missing required fields: {missing}. "
                f"Received keys: {list(data.keys())}"
            )

        # Normalise types
        data["score"] = int(data["score"])
        data["score"] = max(0, min(100, data["score"]))
        data["credit_amount_recommended"] = int(data.get("recommended_credit_amount", 0))
        data["pass_fail"] = bool(data["pass_fail"])

        if isinstance(data["recommendations"], str):
            data["recommendations"] = [data["recommendations"]]

        return data
