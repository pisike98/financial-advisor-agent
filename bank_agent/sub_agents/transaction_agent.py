from google.adk.agents import Agent
from ..tools.customersearch import customer_database_search
from ..models import VertexGemini

transaction_insight_agent = Agent(
    name="transaction_insight_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description=(
        "Derives spend categories and savings rate from a verified "
        "customer's transaction history."
    ),
    instruction="""
You are the Transaction Insight Agent for a banking assistant.

Given a customer_id (already verified by another agent):
1. Call customer_database_search to retrieve transaction history.
2. Bucket spend into categories inferred from transaction
   descriptions/merchant names (e.g. food, travel, utilities, shopping).
3. Compute an approximate savings_rate as:
   (total_inflow - total_outflow) / total_inflow, as a percentage,
   rounded to the nearest integer.

Always respond with strict JSON only, no extra text:
{
  "food_spend": <number>,
  "travel_spend": <number>,
  "other_spend": <number>,
  "savings_rate": <number>
}

If there is not enough transaction history, return:
{"error": "insufficient_transaction_history"}
""",
    tools=[customer_database_search],
)