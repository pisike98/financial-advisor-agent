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

def execute_banking_pipeline(query: str, jwt_token: str = None) -> str:
    """The Root Agent's unified orchestrator pipeline tool.
    
    Acts as the exclusive interface to the Memory Bank. Verifies JWT tokens,
    manages stateful session histories, runs domain sub-agents in parallel,
    audits compliance via suitability guardrails, and polishes copy via the CX agent.
    
    Args:
        query: The user's input question or instruction.
        jwt_token: Optional JWT token string for secure identity propagation.
    """
    print(f"\n[Root Orchestrator] Received user query: '{query}'")
    
    # 1. JWT Authentication and customerId propagation
    # Look for a Bearer token or token pattern inside the query if not explicitly passed
    token = jwt_token
    if not token:
        # Simple extraction regex for bearer token
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
    
    # Create the complete context payload for stateless domain sub-agents
    conversation_context_str = f"Customer ID: {customer_id}\n"
    if summary:
        conversation_context_str += f"Conversation Summary: {summary}\n"
    if history:
        conversation_context_str += "Recent Conversation turns:\n"
        for turn in history[-4:]: # Pass the last 4 turns to keep context dense
            conversation_context_str += f"- User: {turn.get('user', '')}\n- Agent: {turn.get('agent', '')}\n"
            
    # Add current query
    current_payload = f"{conversation_context_str}Current Query: {query}"
    
    # 3. Parallel Execution of Phase 1 Subagents: Profiling and Insights
    print("\n[Root Orchestrator] Starting Phase 1 sub-agents in parallel...")
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
    
    print(f"[Root Orchestrator] Phase 1 completed.\nProfile: {profile_data}\nTransactions: {transactions_data}")
    
    if "error" in profile_data:
        return f"I'm sorry, I was unable to verify your profile details. (Code: {profile_data.get('error')})"
        
    # 4. Parallel Execution of Phase 2 Subagents: Advisory and Product Recommendation
    print("\n[Root Orchestrator] Starting Phase 2 sub-agents in parallel...")
    advisory_prompt = f"""
    Given the following customer metrics:
    - Customer Profile: {json.dumps(profile_data)}
    - Transaction Insights: {json.dumps(transactions_data)}
    - Conversation History & context: {conversation_context_str}
    
    Provide your financial advisory recommendation based on the current user query: '{query}'.
    """
    
    product_prompt = f"""
    Given the following customer metrics:
    - Customer Profile: {json.dumps(profile_data)}
    - Transaction Insights: {json.dumps(transactions_data)}
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
    
    print(f"[Root Orchestrator] Phase 2 completed.\nAdvisory: {advisory_data}\nProducts: {product_data}")
    
    # 5. Phase 3: Suitability & Guardrails Audit
    print("\n[Root Orchestrator] Executing Compliance Guardrails Audit...")
    guardrails_prompt = f"""
    Run your strict suitability, compliance, and eligibility audits on the following:
    - Customer Profile: {json.dumps(profile_data)}
    - Advisory Recommendations: {json.dumps(advisory_data)}
    - Product Recommendations: {json.dumps(product_data.get('recommendations', []))}
    """
    audit_response = run_stateless_agent(suitability_guardrails_agent, guardrails_prompt)
    audit_data = _clean_and_parse_json(audit_response)
    
    print(f"[Root Orchestrator] Guardrails completed. Audit Result:\n{json.dumps(audit_data, indent=2)}")
    
    # 6. Phase 4: Customer Experience Refinement
    print("\n[Root Orchestrator] Refining final customer experience copy...")
    cx_prompt = f"""
    Format the audited financial package into client-facing conversational response:
    - Customer Profile: {json.dumps(profile_data)}
    - Compliance Audit Payload: {json.dumps(audit_data)}
    - Original user query: '{query}'
    """
    final_friendly_text = run_stateless_agent(cx_agent, cx_prompt)
    
    # 7. Stateful Memory Bank persistence (Root Agent only!)
    # Update conversational logs
    history.append({
        "user": query,
        "agent": final_friendly_text,
        "timestamp": datetime_now_iso()
    })
    
    # Generate an updated, dense conversation summary using the current exchange
    updated_summary = f"{summary}\nCustomer asked '{query}' and received recommendations regarding '{advisory_data.get('primary_focus', 'financial planning')}'."
    memory_manager.save_session_context(customer_id, history, updated_summary[:1000])
    
    print("[Root Orchestrator] Securely saved updated conversation history to Memory Bank.")
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
        customer_profile_agent,
        transaction_insight_agent,
        financial_advisory_agent,
        product_recommendation_agent,
        suitability_guardrails_agent,
        cx_agent
    ],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
