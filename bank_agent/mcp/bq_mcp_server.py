import os
import sqlite3
from typing import Dict, Any, List, Optional
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

BQ_DATASET = os.getenv("BQ_DATASET", "")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Initialize FastMCP Server
mcp = FastMCP("BigQuery MCP Server")

def _get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID if PROJECT_ID else None)

@mcp.tool()
def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """Retrieves full customer profile details including demographics, income, occupation, and financial obligations.
    
    Args:
        customer_id: The ID of the customer (e.g. 'C001').
    """
    try:
        if BQ_DATASET:
            client = _get_bq_client()
            query = f"""
                SELECT customer_id, name, dob, postcode, address, age, gender, phone, 
                       income, marital_status, occupation, nationality, employment_status, mortgages
                FROM `{BQ_DATASET}.customers`
                WHERE customer_id = @customer_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)]
            )
            result_df = client.query(query, job_config=job_config).to_dataframe()
            if result_df.empty:
                return {"status": "error", "message": f"Customer ID {customer_id} not found."}
            return result_df.iloc[0].to_dict()
        else:
            conn = sqlite3.connect("bank_data.db")
            query = "SELECT * FROM customers WHERE customer_id = ?"
            result_df = pd.read_sql_query(query, conn, params=[customer_id])
            conn.close()
            if result_df.empty:
                return {"status": "error", "message": f"Customer ID {customer_id} not found."}
            return result_df.iloc[0].to_dict()
            
    except Exception as e:
        return {"status": "error", "message": f"Failed to retrieve customer profile: {str(e)}"}

@mcp.tool()
def get_customer_accounts(customer_id: str) -> List[Dict[str, Any]]:
    """Retrieves all active bank accounts and balances for a given customer ID.
    
    Args:
        customer_id: The ID of the customer (e.g. 'C001').
    """
    try:
        if BQ_DATASET:
            client = _get_bq_client()
            query = f"""
                SELECT account_id, customer_id, product_type, balance
                FROM `{BQ_DATASET}.accounts`
                WHERE customer_id = @customer_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)]
            )
            result_df = client.query(query, job_config=job_config).to_dataframe()
            return result_df.to_dict(orient="records")
        else:
            conn = sqlite3.connect("bank_data.db")
            query = "SELECT * FROM accounts WHERE customer_id = ?"
            result_df = pd.read_sql_query(query, conn, params=[customer_id])
            conn.close()
            return result_df.to_dict(orient="records")
            
    except Exception as e:
        print(f"Error fetching customer accounts: {str(e)}")
        return []

@mcp.tool()
def get_customer_transactions(customer_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves detailed transaction history for all accounts belonging to a specific customer.
    
    Args:
        customer_id: The ID of the customer (e.g. 'C001').
        limit: The maximum number of transactions to retrieve.
    """
    try:
        if BQ_DATASET:
            client = _get_bq_client()
            query = f"""
                SELECT t.account_id, t.description, t.amount, t.type, t.date, t.category, t.is_recurring
                FROM `{BQ_DATASET}.transactions` t
                JOIN `{BQ_DATASET}.accounts` a ON t.account_id = a.account_id
                WHERE a.customer_id = @customer_id
                ORDER BY t.date DESC
                LIMIT @limit
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                    bigquery.ScalarQueryParameter("limit", "INTEGER", limit)
                ]
            )
            result_df = client.query(query, job_config=job_config).to_dataframe()
            return result_df.to_dict(orient="records")
        else:
            conn = sqlite3.connect("bank_data.db")
            query = """
                SELECT t.*
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = ?
                ORDER BY t.date DESC
                LIMIT ?
            """
            result_df = pd.read_sql_query(query, conn, params=[customer_id, limit])
            conn.close()
            return result_df.to_dict(orient="records")
            
    except Exception as e:
        print(f"Error fetching customer transactions: {str(e)}")
        return []

@mcp.tool()
def get_product_catalog(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves the official bank product catalog, optionally filtered by product category.
    
    Args:
        category: Optional category to filter products (e.g. 'savings', 'credit', 'investment', 'insurance').
    """
    try:
        category_filter = ""
        if category:
            category_filter = "WHERE LOWER(category) = @category"
            
        if BQ_DATASET:
            client = _get_bq_client()
            query = f"""
                SELECT product_id, name, category, interest_rate, monthly_fee, access_type, min_opening_balance, description, eligibility
                FROM `{BQ_DATASET}.products`
                {category_filter}
            """
            parameters = []
            if category:
                parameters.append(bigquery.ScalarQueryParameter("category", "STRING", category.lower().strip()))
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            result_df = client.query(query, job_config=job_config).to_dataframe()
            return result_df.to_dict(orient="records")
        else:
            conn = sqlite3.connect("bank_data.db")
            if category:
                query = "SELECT * FROM products WHERE LOWER(category) = ?"
                result_df = pd.read_sql_query(query, conn, params=[category.lower().strip()])
            else:
                query = "SELECT * FROM products"
                result_df = pd.read_sql_query(query, conn)
            conn.close()
            return result_df.to_dict(orient="records")
            
    except Exception as e:
        print(f"Error fetching product catalog: {str(e)}")
        return []

if __name__ == "__main__":
    mcp.run()
