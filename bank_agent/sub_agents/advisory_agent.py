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
  ({persona, income_band, risk_profile})
- transactions: output from the Transaction Insight Agent
  ({food_spend, travel_spend, other_spend, savings_rate})

You may call market_outlook_stub(topic) for market context — it
currently returns placeholder data only ("confidence": 0.0). If you
use it, say explicitly that it's illustrative, not a real signal.

Produce a recommendation that:
1. References the customer's risk_profile and savings_rate.
2. Suggests a general direction (cash reserve, ISA, diversified fund)
   — NOT a specific named product (that's a separate agent's job).
3. Explains your reasoning in 2-3 sentences.

Respond in strict JSON:
{
  "recommendation": "<string>",
  "reasoning": ["<string>", "<string>"],
  "confidence": <number 0-1>
}
""",
    tools=[market_outlook_stub],
)