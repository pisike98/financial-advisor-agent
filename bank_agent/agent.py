import os
from functools import cached_property

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import Client
from .models import VertexGemini

from .observability import (
    after_model_callback,
    before_model_callback,
    setup_observability,
)
from .prompt import AGENT_INSTRUCTION
from .tools.bigquery_tool import run_bigquery_query
from .tools.customersearch import customer_database_search, customer_id_search
from .tools.productsearch import vertex_vector_search
from .tools.ecommerce_tools import lookup_user_orders, check_product_stock, sales_reporting_query

from .sub_agents import (
    customer_profile_agent,
    transaction_insight_agent,
    financial_advisory_agent,
    product_recommendation_agent,
    suitability_guardrails_agent,
)

load_dotenv()

# Initialise OpenTelemetry exporters and the metrics store.
setup_observability()

root_agent = Agent(
    name="bank_agent",
    model=VertexGemini(model="gemini-2.5-flash"),
    description="A helpful banking assistant.",
    instruction=AGENT_INSTRUCTION,
    tools=[customer_id_search, customer_database_search, vertex_vector_search, run_bigquery_query, lookup_user_orders, check_product_stock, sales_reporting_query],
    sub_agents=[
        customer_profile_agent,
        transaction_insight_agent,
        financial_advisory_agent,
        product_recommendation_agent,
        suitability_guardrails_agent,
    ],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
