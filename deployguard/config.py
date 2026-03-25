import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # If risk_score >= RISK_THRESHOLD => block deployment
    RISK_THRESHOLD: float = float(os.getenv("DEPLOYGUARD_RISK_THRESHOLD", "7"))

    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    # Optional, defaults to a generally available Claude Messages API model.
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    CLAUDE_API_URL: str = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/messages")

    # GitLab configuration
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    GITLAB_BASE_URL: str = os.getenv("GITLAB_BASE_URL", "https://gitlab.com/api/v4")

    # Set to "true" to enable local-only mock behavior for GitLab API calls.
    MOCK_GITLAB: bool = os.getenv("DEPLOYGUARD_MOCK_GITLAB", "false").lower() in {"1", "true", "yes", "y"}

    # FastAPI server / orchestration
    DEPLOYGUARD_CONTEXT: str = os.getenv("DEPLOYGUARD_CONTEXT", "deployguard")
    DEPLOYGUARD_TARGET_URL: str = os.getenv("DEPLOYGUARD_TARGET_URL", "")


config = Config()

