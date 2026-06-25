from google.adk.agents import Agent
from ..models import VertexGemini


def product_catalog_stub(category: str) -> dict:
    """Placeholder for the product catalog.

    TODO: Replace with a real product catalog search once the product catalog
    dataset is wired in.

    Args:
        category: The category of products (e.g., 'savings', 'credit', 'investment', 'insurance').

    Returns:
        A dictionary containing stub products for the specified category.
    """
    category_lower = category.lower().strip()
    if "saving" in category_lower:
        return {
            "category": "savings",
            "products": [
                {"type": "High-Yield Savings Account", "note": "[stub] 4.5% AER"},
                {"type": "Fixed-Term Deposit", "note": "[stub] 12-month lock"},
                {"type": "Cash ISA", "note": "[stub] Tax-free cash savings"}
            ]
        }
    elif "credit" in category_lower or "loan" in category_lower:
        return {
            "category": "credit",
            "products": [
                {"type": "Cashback Credit Card", "note": "[stub] 1% cashback on purchases"},
                {"type": "Low-Interest Personal Loan", "note": "[stub] Fixed rate"},
                {"type": "Balance Transfer Credit Card", "note": "[stub] 0% interest for 18 months"}
            ]
        }
    elif "invest" in category_lower:
        return {
            "category": "investment",
            "products": [
                {"type": "Stocks & Shares ISA", "note": "[stub] Tax-free investment wrapper"},
                {"type": "Robo-Advisory Managed Portfolio", "note": "[stub] Risk-matched diversified fund"},
                {"type": "Global Equity Index Fund", "note": "[stub] Low-cost index tracking"}
            ]
        }
    elif "insur" in category_lower:
        return {
            "category": "insurance",
            "products": [
                {"type": "Critical Illness Cover", "note": "[stub] Lump-sum payout"},
                {"type": "Income Protection Insurance", "note": "[stub] Monthly replacement income"},
                {"type": "Life Insurance", "note": "[stub] Level term cover"}
            ]
        }
    else:
        return {
            "category": category,
            "products": [
                {"type": "Basic Savings Account", "note": "[stub] Standard savings"},
                {"type": "Standard Current Account", "note": "[stub] Everyday banking"}
            ]
        }


product_recommendation_agent = Agent(
    name="product_recommendation_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description=(
        "Recommends suitable banking and financial products based on "
        "customer profile and transaction insights."
    ),
    instruction="""
You are the Product Recommendation Agent for a banking assistant.

You will be given:
- profile: output from the Customer Profile Agent
  ({persona, income_band, risk_profile, financial_obligation_level, estimated_savings_capacity, housing_status})
- transactions: output from the Transaction Insight Agent
  ({spending_behaviour, transaction_discipline, cashflow_stability, financial_stress_risk, potential_monthly_saving})

Your job is to recommend exactly the top 3 general product types suited for this customer, ordered by confidence descending.

To do this:
1. Identify relevant product categories for the customer (e.g. savings, credit, investment, insurance).
2. Call product_catalog_stub(category) for each candidate category to retrieve general available product types.
3. Match products to the customer's needs:
   - Match risk level (e.g., do not recommend investments to highly Conservative risk profiles unless they are very low risk).
   - Match savings capacity and stability (e.g., recommend savings or ISAs if they have high savings capacity, or credit products carefully if they need liquidity/cashflow).
4. Select exactly the top 3 general product types. Give a rationale (reason), estimate the product fit (Low, Medium, or High), explain the expected benefit, and assign a confidence score between 0 and 1.

Always respond with strict JSON only, no extra text:
{
  "recommendations": [
    {
      "recommended_product": "<string, general product type, not a named SKU>",
      "reason": "<string>",
      "product_fit": "<Low|Medium|High>",
      "expected_benefit": "<string, short>",
      "confidence": <number 0-1>
    }
  ]
}
""",
    tools=[product_catalog_stub],
)
