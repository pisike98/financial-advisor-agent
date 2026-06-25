from google.adk.agents import Agent
from ..models import VertexGemini


def check_eligibility_stub(income_band: str, risk_profile: str, products: list[str]) -> dict:
    """Placeholder eligibility check.

    TODO: Replace with real product eligibility rules once the
    product catalog dataset is available.
    """
    results = {}
    for product in products:
        results[product] = {
            "eligible": True,
            "checked_rules": ["income_threshold", "risk_alignment"],
            "note": "[stub] Using placeholder eligibility logic.",
        }
    return {
        "eligibility_results": results,
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
- profile: output from Customer Profile Agent
  ({persona, income_band, risk_profile, financial_obligation_level, estimated_savings_capacity, housing_status})
- advisory: output from Financial Advisory Agent
  ({financial_health, primary_focus, advisory_summary, market_outlook, confidence})
- recommendations: output from Product Recommendation Agent
  ({"recommendations": [{"recommended_product", "reason", "product_fit", "expected_benefit", "confidence"}, ...]})

Checks:
1. Risk Alignment: Check if the risk level of each recommended product aligns with profile.risk_profile. Flag any discrepancies.
2. Product Eligibility: Call check_eligibility_stub with the customer's income_band, risk_profile, and the list of recommended_products extracted from the recommendations. If a product is determined to be ineligible, filter it out from final_recommendations.
3. Hallucination/Overpromising: Check the advisory_summary and each product's reason/expected_benefit for any hallucinated, unrealistic, or overly specific guarantees (such as promised percentage returns or risk-free double-digit gains). If any are found, add a flag describing the overpromise.

Output:
- approved: set to true if at least some products or advice are approved and safe, false if the entire set is rejected/unsuitable.
- flags: a list of warnings or validation failure strings.
- final_advisory_summary: the approved advisory_summary string, or null if unapproved.
- final_recommendations: the list of filtered recommendations that passed eligibility checks, keeping the same JSON schema as the product_recommendation_agent's list, or null if none are approved.

Always respond with strict JSON only, no extra text:
{
  "approved": <true|false>,
  "flags": ["<string>", ...],
  "final_advisory_summary": "<string or null>",
  "final_recommendations": [
    {
      "recommended_product": "<string>",
      "reason": "<string>",
      "product_fit": "<Low|Medium|High>",
      "expected_benefit": "<string>",
      "confidence": <number>
    }
  ]
}
""",
    tools=[check_eligibility_stub],
)