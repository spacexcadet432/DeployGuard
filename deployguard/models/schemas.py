from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class GitLabPipelineWebhook(BaseModel):
    """
    Minimal subset of a GitLab pipeline webhook payload.
    GitLab's full schema is large; we only extract fields we need.
    """

    project_id: int = Field(..., description="GitLab project ID")
    commit_sha: str = Field(..., description="Commit SHA for the pipeline")
    pipeline_status: str = Field(..., description="Pipeline status (e.g. success)")
    merge_request_iid: Optional[int] = Field(None, description="Merge request IID (if pipeline is MR-related)")

    @field_validator("pipeline_status")
    @classmethod
    def normalize_pipeline_status(cls, v: str) -> str:
        v2 = (v or "").strip().lower()
        if not v2:
            raise ValueError("pipeline_status must be non-empty")
        return v2


class DiffSummary(BaseModel):
    files_changed: list[str] = Field(default_factory=list)
    total_lines_changed: int = 0


class IncidentMatchResult(BaseModel):
    incidents_by_file: dict[str, int] = Field(default_factory=dict)
    severity_distribution: dict[str, int] = Field(default_factory=dict)
    # Extra context for Claude prompt construction (not required by the spec output contract).
    incident_matches: list[dict[str, Any]] = Field(default_factory=list)


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Recommendation = Literal["block", "allow"]


class RiskIntelligence(BaseModel):
    risk_score: float
    risk_level: RiskLevel
    top_risk_factors: list[str] = Field(default_factory=list)
    recommendation: Recommendation
    rollback_plan: str = ""

