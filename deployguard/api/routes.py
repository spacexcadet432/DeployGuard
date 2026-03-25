from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from deployguard.gitlab.webhook_parser import parse_gitlab_pipeline_webhook
from deployguard.models.schemas import GitLabPipelineWebhook
from deployguard.services.risk_analysis_service import analyze_and_decide
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/webhook/gitlab/pipeline")
async def gitlab_pipeline_webhook(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    try:
        webhook: GitLabPipelineWebhook = parse_gitlab_pipeline_webhook(payload)
    except Exception as e:
        logger.exception("Webhook parse/validation failed: %s", e)
        raise HTTPException(status_code=400, detail="Webhook payload missing required fields")

    if webhook.project_id <= 0 or not webhook.commit_sha:
        raise HTTPException(status_code=400, detail="Webhook payload missing project_id/commit_sha")

    try:
        result = analyze_and_decide(webhook)
        return {"ok": True, "result": result}
    except Exception as e:
        logger.exception("DeployGuard pipeline analysis failed: %s", e)
        raise HTTPException(status_code=500, detail="DeployGuard internal error")

