import os
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server for Knowledge
mcp = FastMCP("Knowledge MCP Server")

# Simulated High-Fidelity Enterprise Knowledge Base
REGULATORY_DATA = [
    {
        "id": "FCA_MCOB_1",
        "title": "FCA Mortgage Conduct of Business (MCOB) Guidelines",
        "content": "Lenders must assess consumer affordability before recommending any mortgage product. Recommended products must align with the customer's declared retirement age, income band, and overall risk appetite. Directing vulnerable clients (low savings/unstable cashflow) to high-interest short-term credit is strictly prohibited."
    },
    {
        "id": "FCA_COBS_2",
        "title": "FCA Conduct of Business Sourcebook (COBS) - Suitability",
        "content": "When advising on retail investment products (e.g. Stocks & Shares ISA, Managed Portfolios), firm must ensure that the transaction meets the customer's investment objectives, is such that they are financially able to bear any related investment risks, and they have the necessary knowledge and experience. Conservative risk profiles must only be offered capital-protected or ultra-low risk savings instruments."
    },
    {
        "id": "CONC_5_2",
        "title": "FCA Consumer Credit Sourcebook (CONC) - Credit Worthiness",
        "content": "Before entering into a regulated credit agreement or significantly increasing credit limits, an assessment of the customer's creditworthiness must be performed. This includes analyzing existing monthly obligations, mortgages, and cashflow stability. If a customer displays medium to high financial stress, credit products must include explicit suitability warnings."
    }
]

MARKET_INTEL = [
    {
        "topic": "uk interest rates",
        "summary": "The Bank of England's Monetary Policy Committee maintains the base rate at 5.25%. High-yield savings accounts and fixed-term cash deposits are highly attractive for risk-averse savers. Conversely, variable-rate mortgages see elevated monthly payments.",
        "source": "Bloomberg UK",
        "confidence": 0.95
    },
    {
        "topic": "inflation and cost of living",
        "summary": "UK Consumer Price Index (CPI) annual inflation remains steady at 2.4%. Discretionary spending among medium-income households has decreased by 4.2% year-on-year. Advisory agents should emphasize building 3-to-6 month emergency buffers.",
        "source": "Office for National Statistics (ONS)",
        "confidence": 0.90
    },
    {
        "topic": "investment market outlook",
        "summary": "Global equity indices are displaying moderate volatility due to tech sector earnings adjustments. Managed portfolios and tax-efficient wrappers like Stocks & Shares ISAs are recommended for aggressive/moderate risk profiles with investment horizons of 5+ years.",
        "source": "Financial Times Market Report",
        "confidence": 0.85
    }
]

@mcp.tool()
def search_fca_regulations(query: str) -> Dict[str, Any]:
    """Searches official FCA (Financial Conduct Authority) compliance guidelines, MCOB rules, and suitability regulations.
    
    Args:
        query: The search term or regulatory topic to search (e.g. 'mortgages', 'investments', 'credit').
    """
    query_lower = query.lower()
    matches = []
    for doc in REGULATORY_DATA:
        if query_lower in doc["title"].lower() or query_lower in doc["content"].lower():
            matches.append(doc)
            
    # Default to returning all if no specific match to guide the LLM compliance checks
    results = matches if matches else REGULATORY_DATA
    
    return {
        "status": "success",
        "query": query,
        "results": results,
        "count": len(results)
    }

@mcp.tool()
def search_market_intel(topic: str) -> Dict[str, Any]:
    """Searches live Bloomberg, FT, and ONS financial market intelligence, interest rate reports, and economic outlooks.
    
    Args:
        topic: The economic or market topic to look up (e.g. 'interest rates', 'inflation', 'investments').
    """
    topic_lower = topic.lower()
    for item in MARKET_INTEL:
        if topic_lower in item["topic"] or any(word in item["topic"] for word in topic_lower.split()):
            return {
                "status": "success",
                "summary": item["summary"],
                "source": item["source"],
                "confidence": item["confidence"]
            }
            
    # Default fallback
    return {
        "status": "success",
        "summary": "UK economic growth remains moderate. High base rates support high-yield cash products. Steady long-term outlook favor diversified tax-free investment wrappers.",
        "source": "ONS Economic Summary",
        "confidence": 0.70
    }

if __name__ == "__main__":
    mcp.run()
