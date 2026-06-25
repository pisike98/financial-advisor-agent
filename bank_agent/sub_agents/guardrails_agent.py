from google.adk.agents import Agent
from ..models import VertexGemini


def check_eligibility_stub(income_band: str, risk_profile: str, product_type: str) -> dict:
    """Placeholder eligibility check.

    TODO: Replace with real product eligibility rules once the
    product catalog dataset is available.
    """
    return {
        "eligible": True,
        "checked_rules": ["income_threshold", "risk_alignment"],
        "note": "[stub] Using placeholder eligibility logic.",
    }


suitability_guardrails_agent = Agent(
    name="suitability_guardrails_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description=(
        "Final checkpoint — validates a recommendation against risk, "
        "income, and eligibility rules before it reaches the customer."
    ),
    instruction="""
You are the Suitability & Guardrails Agent — the last checkpoint.

Given:
- profile: {persona, income_band, risk_profile}
- recommendation: output from the Financial Advisory Agent

Checks:
1. Does the recommendation's risk level match risk_profile? Flag if not.
2. Call check_eligibility_stub with income_band, risk_profile, and the
   product_type implied by the recommendation.
3. Does the recommendation contain anything that sounds like a
   hallucinated or overly specific guarantee (e.g. promised returns)?
   Flag if so.

Respond in strict JSON:
{
  "approved": <true|false>,
  "flags": ["<string>", ...],
  "final_recommendation": "<string if approved, else null>"
}
""",
    tools=[check_eligibility_stub],
)