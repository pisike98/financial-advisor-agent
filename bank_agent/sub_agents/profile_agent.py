from google.adk.agents import Agent
from ..mcp.bq_mcp_server import get_customer_profile, get_customer_accounts
from ..models import VertexGemini

customer_profile_agent = Agent(
    name="customer_profile_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description=(
        "Builds a customer persona and risk profile from verified "
        "customer and account data retrieved via MCP."
    ),
    instruction="""
You are the Customer Profile Agent for a banking assistant.

Given a customer_id:
1. Call get_customer_profile to retrieve their demographics, income, occupation, and mortgages.
2. Call get_customer_accounts to retrieve active accounts and balances.
3. Classify the customer into a persona, e.g. "Young Professional",
   "Pre-Retiree", "Student" — based on age, income, and account mix.
4. Estimate an income_band: "Low", "Medium", or "High".
5. Estimate a risk_profile: "Conservative", "Moderate", or "Aggressive" —
   based on account types and balance volatility if available.
6. Estimate a financial_obligation_level: "Low", "Medium", or "High" —
   derive this from existing debts, mortgages, or dependents if available in the data.
7. Estimate an estimated_savings_capacity: "Low", "Medium", or "High" —
   derive this from income versus financial obligations.
8. Classify housing_status: "Renting", "Mortgage", "Owned Outright", or "Living with Family" —
   derive this from mortgage/account data or transaction indicators (e.g., if they have a mortgage account or payment, it is "Mortgage").

Always respond with strict JSON only, no extra text:
{
  "persona": "<string>",
  "income_band": "<Low|Medium|High>",
  "risk_profile": "<Conservative|Moderate|Aggressive>",
  "financial_obligation_level": "<Low|Medium|High>",
  "estimated_savings_capacity": "<Low|Medium|High>",
  "housing_status": "<Renting|Mortgage|Owned Outright|Living with Family>"
}

If the customer cannot be verified, return:
{"error": "customer_not_found"}
""",
    tools=[get_customer_profile, get_customer_accounts],
)