from __future__ import annotations

import os
import sys
from typing import Any

import httpx


def main() -> int:
    server_url = os.getenv("DEPLOYGUARD_SERVER_URL", "http://127.0.0.1:8000")
    webhook_url = server_url.rstrip("/") + "/webhook/gitlab/pipeline"

    # Mock GitLab webhook payload (minimal fields DeployGuard expects).
    payload: dict[str, Any] = {
        "project": {"id": int(os.getenv("MOCK_PROJECT_ID", "123"))},
        "checkout_sha": os.getenv("MOCK_COMMIT_SHA", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"),
        "object_attributes": {"status": "success"},
        "merge_request_iid": int(os.getenv("MOCK_MR_IID", "1")),
    }

    # Send webhook.
    with httpx.Client(timeout=30) as client:
        resp = client.post(webhook_url, json=payload)
        print("Status:", resp.status_code)
        try:
            print(resp.json())
        except Exception:
            print(resp.text)

    return 0 if resp.status_code < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())

