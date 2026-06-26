import os
from typing import Dict, Any, List, Optional
import asyncio

# Direct programmatic imports from our MCP server modules for maximum speed and reliability
from .bq_mcp_server import (
    get_customer_profile,
    get_customer_accounts,
    get_customer_transactions,
    get_product_catalog
)
from .knowledge_mcp_server import (
    search_fca_regulations,
    search_market_intel
)

class MCPClientOrchestrator:
    """Standardized MCP Client Orchestrator.
    
    Provides a clean, unified, pluggable tool interface for LLMs and domain agents
    to execute queries against BigQuery and Knowledge bases, wrapping the underlying
    MCP transport layer.
    """
    
    def __init__(self):
        # Maps tool name to its direct programmatic handler
        self._direct_tools = {
            "get_customer_profile": get_customer_profile,
            "get_customer_accounts": get_customer_accounts,
            "get_customer_transactions": get_customer_transactions,
            "get_product_catalog": get_product_catalog,
            "search_fca_regulations": search_fca_regulations,
            "search_market_intel": search_market_intel
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns the metadata of all registered MCP tools."""
        return [
            {
                "name": "get_customer_profile",
                "description": "Retrieves demographics, income, occupation, and financial obligations for a customer ID.",
                "parameters": {"customer_id": "string"}
            },
            {
                "name": "get_customer_accounts",
                "description": "Retrieves active bank accounts and balances for a given customer ID.",
                "parameters": {"customer_id": "string"}
            },
            {
                "name": "get_customer_transactions",
                "description": "Retrieves transaction history for all accounts of a specific customer.",
                "parameters": {"customer_id": "string", "limit": "integer"}
            },
            {
                "name": "get_product_catalog",
                "description": "Retrieves the official bank product catalog, optionally filtered by category.",
                "parameters": {"category": "string"}
            },
            {
                "name": "search_fca_regulations",
                "description": "Searches official FCA compliance guidelines, MCOB rules, and suitability regulations.",
                "parameters": {"query": "string"}
            },
            {
                "name": "search_market_intel",
                "description": "Searches live Bloomberg, FT, and ONS financial market intelligence and outlooks.",
                "parameters": {"topic": "string"}
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes a registered tool from either BigQuery or Knowledge MCP server.
        
        Args:
            tool_name: The name of the tool to invoke.
            arguments: Dictionary of arguments to pass to the tool.
            
        Returns:
            The raw response payload from the tool.
        """
        if tool_name not in self._direct_tools:
            raise ValueError(f"Tool '{tool_name}' is not registered with this MCP Client.")
            
        handler = self._direct_tools[tool_name]
        try:
            # Handle standard keyword arguments
            return handler(**arguments)
        except Exception as e:
            print(f"Error calling MCP tool '{tool_name}' with arguments {arguments}: {str(e)}")
            return {"status": "error", "message": f"Execution error: {str(e)}"}

# Singleton Instance
mcp_client = MCPClientOrchestrator()
