from __future__ import annotations

from typing import Any, Optional

from deployguard.models.schemas import GitLabPipelineWebhook


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_gitlab_pipeline_webhook(payload: dict[str, Any]) -> GitLabPipelineWebhook:
    """
    Validate minimal payload and extract:
      - project_id
      - commit_sha
      - pipeline_status
      - merge_request_iid (if present)
    """
    project_id: Any = None
    commit_sha: Any = None
    pipeline_status: Any = None
    merge_request_iid: Any = None

    # Common GitLab webhook structure for pipeline hooks.
    project_id = (payload.get("project") or {}).get("id") or payload.get("project_id") or payload.get("object_attributes", {}).get("project_id")
    commit_sha = payload.get("checkout_sha") or payload.get("checkoutSha") or (payload.get("object_attributes") or {}).get("sha") or payload.get("commit_sha")
    pipeline_status = (payload.get("object_attributes") or {}).get("status") or payload.get("status") or payload.get("pipeline_status")

    merge_request_iid = (
        (payload.get("object_attributes") or {}).get("merge_request_iid")
        or (payload.get("merge_request") or {}).get("iid")
        or payload.get("merge_request_iid")
    )

    # Normalize types; let pydantic handle final validation.
    webhook = GitLabPipelineWebhook(
        project_id=int(project_id) if project_id is not None else 0,
        commit_sha=str(commit_sha) if commit_sha is not None else "",
        pipeline_status=str(pipeline_status) if pipeline_status is not None else "",
        merge_request_iid=_safe_int(merge_request_iid),
    )
    return webhook

