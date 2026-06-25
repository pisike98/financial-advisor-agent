from google.adk.agents import Agent
from ..models import VertexGemini


def market_outlook_stub(topic: str) -> dict:
    """Placeholder for the Market Intelligence Agent's output.

    TODO: Replace with a real call once Bloomberg/UK market reports
    are loaded into Vertex AI Search.

    Args:
        topic: Short topic string, e.g. "UK interest rates".

    Returns:
        Placeholder market summary with confidence 0.0 so the
        advisory agent knows not to treat it as real signal.
    """
    return {
        "summary": f"[stub] No live market data yet for '{topic}'.",
        "source": "placeholder",
        "confidence": 0.0,
    }


financial_advisory_agent = Agent(
    name="financial_advisory_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description=(
        "Combines customer profile, transaction insights, and market "
        "intelligence into a personalised financial recommendation."
    ),
    instruction="""
You are the Financial Advisory Agent — the "brain" of the system.

You will be given:
- profile: output from the Customer Profile Agent
  ({persona, income_band, risk_profile, financial_obligation_level, estimated_savings_capacity, housing_status})
- transactions: output from the Transaction Insight Agent
  ({spending_behaviour, transaction_discipline, cashflow_stability, financial_stress_risk, potential_monthly_saving})

You may call market_outlook_stub(topic) for market context — it
currently returns placeholder data only ("confidence": 0.0). If you
use it, say explicitly that it's illustrative, not a real signal.

Produce an advisory recommendation that determines:
1. financial_health: "Poor", "Fair", "Good", or "Excellent" — reflecting their savings capacity, stress risk, and cashflow stability.
2. primary_focus: E.g., "Debt reduction", "Build emergency fund", "Investment growth", "Mortgage planning" — based on their profile and transaction indicators.
3. advisory_summary: A 2-3 sentence personalized advisory summary summarizing their financial status, stability, and recommending a general direction (such as building savings or debt reduction). Do NOT name specific products.
4. market_outlook: Include context from calling market_outlook_stub, or default to "No live market data" if not queried.
5. confidence: A confidence score between 0 and 1.

Always respond with strict JSON only, no extra text:
{
  "financial_health": "<Poor|Fair|Good|Excellent>",
  "primary_focus": "<string, e.g. 'Debt reduction', 'Build emergency fund'>",
  "advisory_summary": "<string, 2-3 sentences>",
  "market_outlook": "<string, from market_outlook_stub or 'No live market data'>",
  "confidence": <number 0-1>
}
""",
    tools=[market_outlook_stub],
)