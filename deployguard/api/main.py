from __future__ import annotations

from fastapi import FastAPI

from deployguard.api.routes import router as deployguard_router
from deployguard.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="DeployGuard",
    description="Autonomous AI deployment risk intelligence agent (hackathon MVP).",
)

app.include_router(deployguard_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}

