from __future__ import annotations

from deployguard.config import config


def decide(risk_score: float) -> str:
    """
    If risk_score >= RISK_THRESHOLD => block else allow.
    """
    if float(risk_score) >= float(config.RISK_THRESHOLD):
        return "block"
    return "allow"

