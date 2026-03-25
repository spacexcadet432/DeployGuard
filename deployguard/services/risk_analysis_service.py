from __future__ import annotations

from typing import Any

from deployguard.agent.risk_agent import ClaudeRiskAgent
from deployguard.config import config
from deployguard.gitlab.client import get_gitlab_client
from deployguard.memory.incident_store import get_incident_store
from deployguard.engine.decision_engine import decide
from deployguard.engine.report_generator import generate_markdown_report
from deployguard.models.schemas import DiffSummary, GitLabPipelineWebhook, IncidentMatchResult, RiskIntelligence
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_and_decide(webhook: GitLabPipelineWebhook) -> dict[str, Any]:
    """
    Orchestration service (main business logic layer):
      fetch diff -> search incidents -> call Claude -> decision -> post MR comment -> set commit status
    """
    if webhook.pipeline_status != "success":
        logger.info("Pipeline status is %s; skipping analysis.", webhook.pipeline_status)
        return {"skipped": True, "pipeline_status": webhook.pipeline_status}

    gitlab = get_gitlab_client()
    diff: DiffSummary = gitlab.get_commit_diff(project_id=webhook.project_id, sha=webhook.commit_sha)

    incident_store = get_incident_store()
    incident_result: IncidentMatchResult = incident_store.search_incidents(diff.files_changed)

    risk_agent = ClaudeRiskAgent()
    risk: RiskIntelligence = risk_agent.analyze_risk(diff=diff, incident_result=incident_result)

    decision = decide(risk.risk_score)  # "block" | "allow"
    risk_report_md = generate_markdown_report(risk=risk, recommendation=decision)

    # Post MR comment if MR info exists.
    if webhook.merge_request_iid is not None:
        try:
            gitlab.post_mr_comment(
                project_id=webhook.project_id,
                mr_iid=webhook.merge_request_iid,
                markdown_message=risk_report_md,
            )
        except Exception as e:
            logger.exception("Failed posting MR comment: %s", e)

    # Commit status: set FAILED if risk high.
    commit_state = "failed" if decision == "block" else "success"
    try:
        gitlab.set_commit_status(project_id=webhook.project_id, sha=webhook.commit_sha, state=commit_state)
    except Exception as e:
        logger.exception("Failed setting commit status: %s", e)

    return {
        "skipped": False,
        "diff": diff.model_dump(),
        "incident_result": incident_result.model_dump(),
        "risk": risk.model_dump(),
        "decision": decision,
        "commit_state": commit_state,
    }

