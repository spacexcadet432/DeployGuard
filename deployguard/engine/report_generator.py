from __future__ import annotations

from deployguard.models.schemas import RiskIntelligence


def generate_markdown_report(risk: RiskIntelligence, recommendation: str) -> str:
    risk_level = risk.risk_level
    risk_score = risk.risk_score

    top_factors = risk.top_risk_factors or []
    top_factors_md = "\n".join([f"- {f}" for f in top_factors]) if top_factors else "- (none provided)"

    return (
        "🚨 DeployGuard Risk Analysis\n\n"
        f"Risk Score: {risk_score:.1f} / 10\n"
        f"Risk Level: {risk_level}\n\n"
        "Top Factors:\n"
        f"{top_factors_md}\n\n"
        "Recommendation:\n"
        f"{'BLOCKED' if recommendation == 'block' else 'ALLOWED'}\n\n"
        f"Rollback Plan:\n{risk.rollback_plan or '- (not provided)'}\n"
    )

