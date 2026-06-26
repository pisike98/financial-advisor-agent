import os
from typing import Any, List, Dict, Callable
from google.genai import Client
from google.genai import types
from google.adk.agents import Agent
from ..mcp.mcp_client import mcp_client

# Initialize GenAI Client using Vertex AI
def get_genai_client() -> Client:
    return Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    )

def run_stateless_agent(agent: Agent, prompt: str) -> str:
    """Executes an ADK agent in a completely stateless manner.
    
    Loads its instruction, configures its registered tools, executes the GenAI 
    model content generation, resolves tool/function calls, and returns the 
    final text response.
    
    Args:
        agent: The ADK Agent instance.
        prompt: The user query or context payload.
        
    Returns:
        The final text response from the agent.
    """
    client = get_genai_client()
    
    # Map of tool names to actual functions
    tool_map: Dict[str, Callable] = {}
    mcp_tools_metadata = mcp_client.list_tools()
    
    # Standardize tools: use the agent's own registered tools
    for tool in getattr(agent, "tools", []):
        if hasattr(tool, "__name__"):
            tool_map[tool.__name__] = tool
        elif hasattr(tool, "name"):
            tool_map[tool.name] = tool

    # Convert python functions to GenAI-compatible tool definitions
    # Note: Vertex GenAI SDK can auto-generate schemas from Python type hints
    genai_tools = list(tool_map.values())
    
    # We construct the execution chat content
    system_instruction = getattr(agent, "instruction", "")
    
    # Create the config
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=genai_tools if genai_tools else None,
        temperature=0.0 # Strict and deterministic for agent pipelines
    )
    
    # Start the conversation loop (manages function call exchanges)
    contents = [prompt]
    
    max_turns = 10
    for turn in range(max_turns):
        print(f"[{agent.name}] Turn {turn + 1}...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )
        
        # Check if the model wants to call a function
        function_calls = response.function_calls
        if not function_calls:
            # No tool call, we have our final text response!
            return response.text or ""
            
        # We have function calls, execute them and feed back the results
        # Add the model's message (which contains the function calls) to history
        contents.append(response.candidates[0].content)
        
        # Build the tool response content block
        tool_responses = []
        for call in function_calls:
            name = call.name
            args = call.args
            call_id = call.id
            
            print(f"[{agent.name}] Calling tool '{name}' with args {args}...")
            
            if name in tool_map:
                try:
                    # Execute the tool
                    result = tool_map[name](**args)
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"
            else:
                result = f"Error: Tool '{name}' not found."
                
            print(f"[{agent.name}] Tool '{name}' returned: {str(result)[:200]}...")
            
            # Format as Part object with FunctionResponse
            tool_responses.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result},
                    id=call_id
                )
            )
            
        # Add the function responses back to history
        contents.append(
            types.Content(
                role="user",
                parts=tool_responses
            )
        )
        
    raise RuntimeError(f"[{agent.name}] Reached maximum tool execution turns limit ({max_turns}).")
