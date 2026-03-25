from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deployguard.models.schemas import DiffSummary, IncidentMatchResult


class PromptBuilder:
    @staticmethod
    def build_user_prompt(
        diff: DiffSummary,
        incident_result: IncidentMatchResult,
    ) -> str:
        deployment_time = datetime.now(timezone.utc).isoformat()
        commit_size = {
            "total_lines_changed": diff.total_lines_changed,
            "files_changed_count": len(diff.files_changed),
        }

        prompt: dict[str, Any] = {
            "diff_summary": {
                "files_changed": diff.files_changed,
                "total_lines_changed": diff.total_lines_changed,
            },
            "incident_matches": {
                "incidents_by_file": incident_result.incidents_by_file,
                "severity_distribution": incident_result.severity_distribution,
                "incident_matches": incident_result.incident_matches,
            },
            "deployment_time": deployment_time,
            "commit_size": commit_size,
            "rules": {
                "risk_score_range": "0 to 10",
                "risk_level_mapping": "LOW/MEDIUM/HIGH based on risk_score",
                "recommendation": "Use block when risk_level is HIGH",
            },
        }

        # Instruct Claude to return strict JSON only.
        return (
            "You are DeployGuard, an autonomous deployment risk intelligence agent.\n"
            "Analyze the change and incident memory, then return ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "risk_score": float,\n'
            '  "risk_level": "LOW|MEDIUM|HIGH",\n'
            '  "top_risk_factors": string[],\n'
            '  "recommendation": "block|allow",\n'
            '  "rollback_plan": string\n'
            "}\n\n"
            "Input JSON:\n"
            f"{prompt}"
        )

