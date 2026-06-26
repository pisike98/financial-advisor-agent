import os
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from google.adk.agents import Agent
from .models import VertexGemini
from .prompt import AGENT_INSTRUCTION

# Centralized Observability & Callbacks
from .observability import (
    after_model_callback,
    before_model_callback,
    setup_observability,
)

# Enterprise Core Layers
from .auth import verify_and_extract_customer_id, create_mock_jwt
from .memory import MemoryBankManager
from .sub_agents import (
    customer_profile_agent,
    transaction_insight_agent,
    financial_advisory_agent,
    product_recommendation_agent,
    suitability_guardrails_agent,
    cx_agent
)
from .sub_agents.runner import run_stateless_agent

# Initialize environment & observability
load_dotenv()
setup_observability()

def _clean_and_parse_json(text: str) -> dict:
    """Robustly cleans and parses JSON from model output, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"^(?:```json|```)\s*(.*?)\s*```$", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
            
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {str(e)} for text: {text}")
        # Return a structure to prevent subsequent crashes
        return {"error": "invalid_json_payload", "raw_response": text}

def execute_banking_pipeline(query: str, jwt_token: str = None, intent: str = None) -> str:
    """The Root Agent's unified orchestrator pipeline tool.
    
    Acts as the exclusive interface to the Memory Bank. Verifies JWT tokens,
    manages stateful session histories, runs domain sub-agents selectively based on intent,
    audits compliance via suitability guardrails, and polishes copy via the CX agent.
    
    Args:
        query: The user's input question or instruction.
        jwt_token: Optional JWT token string for secure identity propagation.
        intent: Optional classified intent ('identity' | 'transaction' | 'advice' | 'products')
    """
    print(f"\n[Root Orchestrator] Received user query: '{query}' with intent: '{intent}'")
    
    # 1. JWT Authentication and customerId propagation
    token = jwt_token
    if not token:
        token_match = re.search(r"bearer\s+([a-zA-Z0-9\-\._~\+\/]+=*)", query, re.IGNORECASE)
        if token_match:
            token = token_match.group(1)
            
    if not token:
        print("[Root Orchestrator] No JWT token provided. Automatically generating a mock JWT for Customer C001 (Alice Thornton)...")
        token = create_mock_jwt("C001")
        
    customer_id = verify_and_extract_customer_id(token)
    if not customer_id:
        return "ERROR: Authentication failed. Invalid or expired JWT token. Access Denied."
        
    print(f"[Root Orchestrator] Securely authenticated Customer ID: '{customer_id}'")
    
    # 2. Centralized Stateful Memory Bank retrieval (Root Agent only!)
    memory_manager = MemoryBankManager()
    session_context = memory_manager.get_session_context(customer_id)
    history = session_context.get("history", [])
    summary = session_context.get("summary", "")
    
    print(f"[Root Orchestrator] Memory Bank retrieved: {len(history)} past exchanges, Summary: '{summary}'")
    
    # Auto-classify intent if not explicitly provided as a robust fallback
    if not intent:
        lower_query = query.lower()
        if any(w in lower_query for w in ["name", "who am i", "my profile", "demographics", "postcode", "address", "phone", "post code"]):
            intent = "identity"
        elif any(w in lower_query for w in ["transaction", "spend", "purchase", "buying", "statement", "history", "card", "bought"]):
            intent = "transaction"
        elif any(w in lower_query for w in ["recommend", "product", "saving account", "isa", "mortgage", "credit card", "loan", "fit"]):
            intent = "products"
        elif any(w in lower_query for w in ["advice", "budget", "financial health", "planning", "outlook", "help"]):
            intent = "advice"
        else:
            intent = "advice" # Default fallback
            
    print(f"[Root Orchestrator] Routed Query Intent: '{intent}'")

    # Create the complete context payload for stateless domain sub-agents
    conversation_context_str = f"Customer ID: {customer_id}\n"
    if summary:
        conversation_context_str += f"Conversation Summary: {summary}\n"
    if history:
        conversation_context_str += "Recent Conversation turns:\n"
        for turn in history[-4:]:
            conversation_context_str += f"- User: {turn.get('user', '')}\n- Agent: {turn.get('agent', '')}\n"

    # ==================== ROUTING EXECUTION PATHS ====================

    # --- PATH A: IDENTITY / PROFILE ONLY ---
    if intent == "identity":
        print("[Root Orchestrator] Executing Identity Path (customer_profile_agent only)...")
        profile_response = run_stateless_agent(
            customer_profile_agent, 
            f"Please generate the profile for Customer ID: {customer_id}"
        )
        profile_data = _clean_and_parse_json(profile_response)
        print(f"[Root Orchestrator] Identity Path completed. Profile Data: {profile_data}")
        
        if "error" in profile_data:
            return f"I'm sorry, I was unable to verify your profile details. (Code: {profile_data.get('error')})"
            
        name = profile_data.get("name", "Valued Customer")
        persona = profile_data.get("persona", "Pre-Retiree")
        risk = profile_data.get("risk_profile", "Moderate")
        income = profile_data.get("income_band", "Medium")
        obligations = profile_data.get("financial_obligation_level", "Medium")
        savings = profile_data.get("estimated_savings_capacity", "Medium")
        housing = profile_data.get("housing_status", "Mortgage")

        final_friendly_text = f"""### 👤 Customer Identity Profile Verified

Hello **{name}**, 

Welcome back! Here is a summary of your verified demographics and profile details on file:

| Profile Metric | Value |
| :--- | :--- |
| **Persona Group** | {persona} |
| **Risk Profile Category** | {risk} |
| **Annual Income Band** | {income} |
| **Financial Obligations** | {obligations} |
| **Estimated Savings Capacity** | {savings} |
| **Housing Status** | {housing} |

*If any of these details are incorrect or outdated, please contact our branch customer support team.*
"""
        # Save exchange in Memory Bank
        history.append({
            "user": query,
            "agent": final_friendly_text,
            "timestamp": datetime_now_iso()
        })
        updated_summary = f"{summary}\nCustomer verified identity and demographics under name: {name}."
        memory_manager.save_session_context(customer_id, history, updated_summary[:1000])
        return final_friendly_text

    # --- PATH B: TRANSACTION INSIGHTS ONLY ---
    elif intent == "transaction":
        print("[Root Orchestrator] Executing Transaction Path (transaction_insight_agent only)...")
        transactions_response = run_stateless_agent(
            transaction_insight_agent, 
            f"Please analyze transactions for Customer ID: {customer_id}"
        )
        transactions_data = _clean_and_parse_json(transactions_response)
        print(f"[Root Orchestrator] Transaction Path completed. Data: {transactions_data}")
        
        if "error" in transactions_data:
            return f"I'm sorry, I was unable to retrieve your recent transaction details. (Code: {transactions_data.get('error')})"
            
        spend_by_cat = transactions_data.get("spend_by_category", {})
        top_cat = transactions_data.get("top_spending_category", "N/A")
        top_amt = transactions_data.get("top_spending_category_amount", 0.0)
        recent_summary = transactions_data.get("recent_transactions_summary", "No recent transactions found.")
        discipline = transactions_data.get("transaction_discipline", "Medium")
        stability = transactions_data.get("cashflow_stability", "Stable")
        stress = transactions_data.get("financial_stress_risk", "Low")
        savings = transactions_data.get("potential_monthly_saving", 0.0)

        # Format category spend breakdown table dynamically
        breakdown_rows = ""
        for cat, amt in spend_by_cat.items():
            if amt > 0:
                breakdown_rows += f"| **{cat}** | £{amt:,.2f} |\n"
        if not breakdown_rows:
            breakdown_rows = "| *No category spending data available* | |"

        final_friendly_text = f"""### 📊 Transaction Analytics & Spend Breakdown

Here is a detailed, category-specific breakdown of your recent spending and transaction activity:

#### 📂 Spend Categories
| Expense Category | Total Spent |
| :--- | :--- |
{breakdown_rows}

* 🔴 **Highest Spend Area:** **{top_cat}** (Spent: **£{top_amt:,.2f}**)
* 💡 **Monthly Savings Potential:** **£{savings:,.2f}** (Estimated monthly savings with optimized spending)

#### 📉 Cashflow & Behavioral Indicators
* **Spending Persona:** *{transactions_data.get('spending_behaviour', 'Standard Spender')}*
* **Cashflow Stability:** **{stability}**
* **Account Discipline:** **{discipline}**
* **Financial Stress Risk:** **{stress}**

#### 🕒 Recent Activity Summary
{recent_summary}
"""
        # Save exchange in Memory Bank
        history.append({
            "user": query,
            "agent": final_friendly_text,
            "timestamp": datetime_now_iso()
        })
        updated_summary = f"{summary}\nCustomer viewed transaction history and analytics. Top spend category is {top_cat}."
        memory_manager.save_session_context(customer_id, history, updated_summary[:1000])
        return final_friendly_text

    # --- PATH C: FINANCIAL ADVICE ONLY (No product recommendations) ---
    elif intent == "advice":
        print("[Root Orchestrator] Executing Advice Path (profile, transactions, and advisory only)...")
        # Step 1: Parallel Profiling and Transaction insights
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_profile = executor.submit(
                run_stateless_agent, 
                customer_profile_agent, 
                f"Please generate the profile for Customer ID: {customer_id}"
            )
            future_transactions = executor.submit(
                run_stateless_agent, 
                transaction_insight_agent, 
                f"Please analyze transactions for Customer ID: {customer_id}"
            )
            profile_response = future_profile.result()
            transactions_response = future_transactions.result()
            
        profile_data = _clean_and_parse_json(profile_response)
        transactions_data = _clean_and_parse_json(transactions_response)
        
        if "error" in profile_data:
            return f"I'm sorry, I was unable to verify your profile details. (Code: {profile_data.get('error')})"
            
        # Step 2: Advisory
        advisory_prompt = f"""
        Given the following customer metrics:
        - Customer Profile: {json.dumps(profile_data)}
        - Transaction Insights: {json.dumps(transactions_data)}
        - Conversation History & context: {conversation_context_str}
        
        Provide your financial advisory recommendation based on the current user query: '{query}'.
        """
        advisory_response = run_stateless_agent(financial_advisory_agent, advisory_prompt)
        advisory_data = _clean_and_parse_json(advisory_response)
        
        # Step 3: Fast, bypass suitability_guardrails LLM call (since no products are recommended)
        # Directly construct approved advisory summary
        audit_data = {
            "approved": True,
            "flags": [],
            "final_advisory_summary": advisory_data.get("advisory_summary", "Review your general savings and budget structure."),
            "final_recommendations": []
        }
        
        # Step 4: Formatting final copy via CX Agent
        cx_prompt = f"""
        Format the audited financial package into client-facing conversational response:
        - Customer Profile: {json.dumps(profile_data)}
        - Compliance Audit Payload: {json.dumps(audit_data)}
        - Original user query: '{query}'
        """
        final_friendly_text = run_stateless_agent(cx_agent, cx_prompt)
        
        # Update Memory Bank
        history.append({
            "user": query,
            "agent": final_friendly_text,
            "timestamp": datetime_now_iso()
        })
        updated_summary = f"{summary}\nCustomer received general financial advice on: {advisory_data.get('primary_focus', 'financial health')}."
        memory_manager.save_session_context(customer_id, history, updated_summary[:1000])
        return final_friendly_text

    # --- PATH D: PRODUCT RECOMMENDATIONS (Full pipeline with Compliance Audit) ---
    else:
        print("[Root Orchestrator] Executing Full Product Recommendation Path...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_profile = executor.submit(
                run_stateless_agent, 
                customer_profile_agent, 
                f"Please generate the profile for Customer ID: {customer_id}"
            )
            future_transactions = executor.submit(
                run_stateless_agent, 
                transaction_insight_agent, 
                f"Please analyze transactions for Customer ID: {customer_id}"
            )
            profile_response = future_profile.result()
            transactions_response = future_transactions.result()
            
        profile_data = _clean_and_parse_json(profile_response)
        transactions_data = _clean_and_parse_json(transactions_response)
        
        if "error" in profile_data:
            return f"I'm sorry, I was unable to verify your profile details. (Code: {profile_data.get('error')})"
            
        advisory_prompt = f"""
        Given the following customer metrics:
        - Customer Profile: {json.dumps(profile_data)}
        - Transaction Insights: {json.dumps(transactions_data)}
        - Conversation History & context: {conversation_context_str}
        
        Provide your financial advisory recommendation based on the current user query: '{query}'.
        """
        product_prompt = f"""
        Given the following customer metrics:
        - profile: {json.dumps(profile_data)}
        - transactions: {json.dumps(transactions_data)}
        - Conversation History & context: {conversation_context_str}
        
        Select the top 3 optimal bank product recommendations aligned with their profile and risk level for query: '{query}'.
        """
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_advisory = executor.submit(run_stateless_agent, financial_advisory_agent, advisory_prompt)
            future_product = executor.submit(run_stateless_agent, product_recommendation_agent, product_prompt)
            advisory_response = future_advisory.result()
            product_response = future_product.result()
            
        advisory_data = _clean_and_parse_json(advisory_response)
        product_data = _clean_and_parse_json(product_response)
        
        # Execute Compliance Guardrails Audit (essential for product recommendations!)
        guardrails_prompt = f"""
        Run your strict suitability, compliance, and eligibility audits on the following:
        - profile: {json.dumps(profile_data)}
        - advisory: {json.dumps(advisory_data)}
        - recommendations: {json.dumps({"recommendations": product_data.get('recommendations', [])})}
        """
        audit_response = run_stateless_agent(suitability_guardrails_agent, guardrails_prompt)
        audit_data = _clean_and_parse_json(audit_response)
        
        # Customer Experience formatting
        cx_prompt = f"""
        Format the audited financial package into client-facing conversational response:
        - Customer Profile: {json.dumps(profile_data)}
        - Compliance Audit Payload: {json.dumps(audit_data)}
        - Original user query: '{query}'
        """
        final_friendly_text = run_stateless_agent(cx_agent, cx_prompt)
        
        # Update Memory Bank
        history.append({
            "user": query,
            "agent": final_friendly_text,
            "timestamp": datetime_now_iso()
        })
        updated_summary = f"{summary}\nCustomer requested and received product recommendations. Products audited and processed."
        memory_manager.save_session_context(customer_id, history, updated_summary[:1000])
        return final_friendly_text

def datetime_now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()

# Wrap and export root_agent so that ADK Discovery detects it
root_agent = Agent(
    name="bank_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description="A multi-agent, enterprise-grade stateful financial advisor orchestrator.",
    instruction=AGENT_INSTRUCTION,
    tools=[execute_banking_pipeline],
    sub_agents=[
        financial_advisory_agent,
        product_recommendation_agent,
        suitability_guardrails_agent,
        cx_agent
    ],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
