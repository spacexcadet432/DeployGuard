from __future__ import annotations

import os
from typing import Any

import httpx

from deployguard.config import config
from deployguard.models.schemas import DiffSummary
from deployguard.utils.diff_parser import parse_commit_diff_simplified
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)


class GitLabClient:
    def __init__(self) -> None:
        self._base_url = config.GITLAB_BASE_URL.rstrip("/")
        self._token = config.GITLAB_TOKEN
        self._mock = config.MOCK_GITLAB

    def _headers(self) -> dict[str, str]:
        if self._token:
            return {"PRIVATE-TOKEN": self._token}
        return {}

    def _require_token(self) -> None:
        if self._mock:
            return
        if not self._token:
            raise RuntimeError("GITLAB_TOKEN is not set (and MOCK_GITLAB is false).")

    def get_commit_diff(self, project_id: int, sha: str) -> DiffSummary:
        """
        Fetch commit diff using GitLab API and return simplified DiffSummary.
        """
        if self._mock:
            logger.info("MOCK_GITLAB enabled: returning sample diff.")
            return DiffSummary(
                files_changed=["auth/login.py", "auth/token_utils.py"],
                total_lines_changed=48,
            )

        self._require_token()
        url = f"{self._base_url}/projects/{project_id}/repository/commits/{sha}"
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=self._headers())
            resp.raise_for_status()
            commit_json: dict[str, Any] = resp.json()
        return parse_commit_diff_simplified(commit_json)

    def post_mr_comment(self, project_id: int, mr_iid: int, markdown_message: str) -> None:
        """
        Post a markdown comment to the merge request.
        """
        if self._mock:
            logger.info("MOCK_GITLAB enabled: skipping MR comment POST.")
            logger.info("MR comment preview: %s", markdown_message[:300].replace("\n", " "))
            return

        self._require_token()
        url = f"{self._base_url}/projects/{project_id}/merge_requests/{mr_iid}/notes"
        body = {"body": markdown_message}
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=self._headers(), json=body)
            resp.raise_for_status()

    def set_commit_status(self, project_id: int, sha: str, state: str) -> None:
        """
        Set commit status state.

        State values: "success" | "failed"
        """
        if self._mock:
            logger.info("MOCK_GITLAB enabled: skipping commit status POST.")
            logger.info("Set status for %s to %s", sha, state)
            return

        self._require_token()
        url = f"{self._base_url}/projects/{project_id}/statuses/{sha}"

        description = "DeployGuard blocked risky deployment." if state == "failed" else "DeployGuard allowed deployment."
        payload: dict[str, Any] = {
            "state": state,
            "context": config.DEPLOYGUARD_CONTEXT,
            "description": description,
        }
        if config.DEPLOYGUARD_TARGET_URL:
            payload["target_url"] = config.DEPLOYGUARD_TARGET_URL

        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()


def get_gitlab_client() -> GitLabClient:
    # Kept as a factory to make swapping mock strategies straightforward.
    return GitLabClient()

