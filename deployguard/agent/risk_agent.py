from __future__ import annotations

import json
from typing import Any

import httpx

from deployguard.config import config
from deployguard.models.schemas import DiffSummary, IncidentMatchResult, RiskIntelligence
from deployguard.agent.prompt_builder import PromptBuilder
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeRiskAgent:
    def __init__(self) -> None:
        self._api_key = config.CLAUDE_API_KEY
        self._api_url = config.CLAUDE_API_URL
        self._model = config.CLAUDE_MODEL

    def _require_key(self) -> None:
        if not self._api_key:
            raise RuntimeError("CLAUDE_API_KEY is not set.")

    def _extract_text_from_claude_response(self, resp_json: dict[str, Any]) -> str:
        # Anthropics messages response structure:
        # { "content": [ { "type": "text", "text": "..." } ], ... }
        content = resp_json.get("content") or []
        if not isinstance(content, list) or not content:
            return ""
        first = content[0]
        if isinstance(first, dict) and first.get("type") == "text":
            return str(first.get("text") or "")
        # fallback: try to find any text field
        for item in content:
            if isinstance(item, dict) and "text" in item:
                return str(item.get("text") or "")
        return ""

    def _fallback_invalid_claude_response(self) -> RiskIntelligence:
        # Spec: If Claude response invalid => fallback risk_score = 5
        risk_score = 5.0
        risk_level = "MEDIUM"
        return RiskIntelligence(
            risk_score=risk_score,
            risk_level=risk_level,
            top_risk_factors=[],
            recommendation="allow",
            rollback_plan="",
        )

    def _heuristic_when_claude_unavailable(self, incident_result: IncidentMatchResult) -> RiskIntelligence:
        """
        Deterministic, hackathon-friendly fallback when Claude API can't be called.
        We only apply this when CLAUDE_API_KEY is missing; invalid Claude JSON still
        follows the spec-defined risk_score=5 behavior.
        """
        high_count = int(incident_result.severity_distribution.get("high") or 0)
        med_count = int(incident_result.severity_distribution.get("medium") or 0)

        # Rank top factors by number of past incidents.
        incidents_by_file = incident_result.incidents_by_file or {}
        ranked_files = sorted(incidents_by_file.items(), key=lambda kv: kv[1], reverse=True)
        top_factors = [f"{path} (incidents: {count})" for path, count in ranked_files[:5]]

        if high_count > 0:
            return RiskIntelligence(
                risk_score=9.0,
                risk_level="HIGH",
                top_risk_factors=top_factors,
                recommendation="block",
                rollback_plan="- Roll back to the last known good commit.\n- Re-run auth/smoke tests and token/session regression checks.",
            )
        if med_count > 0 or ranked_files:
            return RiskIntelligence(
                risk_score=6.0,
                risk_level="MEDIUM",
                top_risk_factors=top_factors,
                recommendation="allow",
                rollback_plan="- Deploy behind a feature flag.\n- Monitor error rates and revert if regressions are detected.",
            )
        return RiskIntelligence(
            risk_score=3.0,
            risk_level="LOW",
            top_risk_factors=[],
            recommendation="allow",
            rollback_plan="",
        )

    @staticmethod
    def _try_parse_json_strict(text: str) -> dict[str, Any]:
        """
        Claude should output strict JSON. If it includes extra text, attempt best-effort extraction.
        """
        trimmed = (text or "").strip()
        if not trimmed:
            raise ValueError("Empty Claude response.")

        # If the response is enclosed in markdown fences, strip them.
        if trimmed.startswith("```"):
            # Remove ```json or ``` fences
            trimmed = trimmed.strip("`")
            # After strip, the content might still include leading "json\n"
            trimmed = trimmed.split("\n", 1)[-1].strip()

        # If it contains surrounding text, extract the first {...} block.
        if "{" in trimmed and "}" in trimmed:
            start = trimmed.find("{")
            end = trimmed.rfind("}")
            candidate = trimmed[start : end + 1]
        else:
            candidate = trimmed

        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON is not an object.")
        return parsed

    def analyze_risk(
        self,
        diff: DiffSummary,
        incident_result: IncidentMatchResult,
    ) -> RiskIntelligence:
        if not self._api_key:
            # Allow local hackathon simulation without requiring external API keys.
            logger.warning("CLAUDE_API_KEY not set; using deterministic heuristic.")
            return self._heuristic_when_claude_unavailable(incident_result=incident_result)

        user_prompt = PromptBuilder.build_user_prompt(diff=diff, incident_result=incident_result)

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 700,
            "temperature": 0.2,
            "system": "Return only valid JSON that matches the requested schema. Do not include any extra keys or commentary.",
            "messages": [{"role": "user", "content": user_prompt}],
        }

        try:
            with httpx.Client(timeout=45) as client:
                resp = client.post(self._api_url, headers=headers, json=payload)
                resp.raise_for_status()
                resp_json: dict[str, Any] = resp.json()
        except Exception as e:
            logger.exception("Claude API request failed: %s", e)
            return self._fallback_invalid_claude_response()

        text = self._extract_text_from_claude_response(resp_json)
        try:
            parsed = self._try_parse_json_strict(text)
            risk = RiskIntelligence(**parsed)
            return risk
        except Exception:
            logger.exception("Invalid Claude JSON; using fallback.")
            return self._fallback_invalid_claude_response()

