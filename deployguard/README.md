# DeployGuard (Hackathon MVP)

## Product Vision
DeployGuard is an autonomous deployment risk intelligence agent that integrates with GitLab pipelines. It blocks risky deployments *before* production by analyzing what changed, matching those changes against historical incident memory, and using Claude to produce structured risk intelligence.

## System Flow (Text Diagram)
1. GitLab pipeline succeeds
2. GitLab sends webhook to DeployGuard: `POST /webhook/gitlab/pipeline`
3. DeployGuard validates payload and extracts `project_id`, `commit_sha`, `pipeline_status`, `merge_request_iid`
4. DeployGuard fetches commit diff from GitLab REST API
5. Diff is simplified to: changed files + total lines changed
6. Incident memory searches historical incidents for matching changed files
7. DeployGuard builds a structured prompt (diff + incident matches + deployment time + commit size)
8. DeployGuard calls Claude API and enforces strict JSON output
9. Decision engine compares `risk_score` to `RISK_THRESHOLD`
10. DeployGuard posts a markdown risk report as an MR comment (if MR IID exists)
11. DeployGuard sets commit status to `failed` (or `success`) to effectively block deployment

## Setup Steps
1. Install dependencies
   - From repo root: `pip install -r deployguard/requirements.txt`
2. Configure environment variables
   - `CLAUDE_API_KEY` (required for real Claude analysis)
   - `GITLAB_TOKEN` (required for real GitLab API integration)
   - Optional: `GITLAB_BASE_URL` (default: `https://gitlab.com/api/v4`)
   - Optional: `DEPLOYGUARD_MOCK_GITLAB=true` (skip real GitLab calls; use local sample diff)

## Simulate Webhook (Local Testing without GitLab)
1. Start the server:
   - `uvicorn deployguard.api.main:app --reload --port 8000`
2. Enable mock GitLab in the server process:
   - `set DEPLOYGUARD_MOCK_GITLAB=true`
3. Run the simulator:
   - `python deployguard/simulate_webhook.py`

You should see the webhook request succeed. With `DEPLOYGUARD_MOCK_GITLAB=true`, DeployGuard will log MR comment + commit status actions instead of calling GitLab.

## Example MR Risk Comment
```md
🚨 DeployGuard Risk Analysis

Risk Score: 7.5 / 10
Risk Level: HIGH

Top Factors:
- auth/login.py has known high-severity incidents

Recommendation: BLOCKED

Rollback Plan:
- Roll back to the last known good commit and replay the login smoke test suite.
```

## Example Incident Dataset (`incidents.json`)
```json
[
  {
    "file_path": "auth/login.py",
    "incident_date": "2024-12-12",
    "severity": "high",
    "description": "Login outage due to token bug"
  }
]
```

## Hackathon Positioning
DeployGuard demonstrates a realistic DevTools workflow:
- pipeline webhook ingestion
- commit diff retrieval
- incident-memory search
- strict-JSON LLM risk intelligence
- deterministic block/allow decision
- commit status + MR reporting integration

