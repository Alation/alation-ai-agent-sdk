"""
Customer identification agent that retrieves customer information using Alation metadata and SQL execution.
"""

import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import Tool

from schemas import CustomerState, CUSTOMER_PROFILE_SIGNATURE
from tools import get_alation_tools, execute_sql
from config import LLM_MODEL, USE_MOCK_DATA


def create_identification_agent():
    """
    Create an agent for identifying customers using Alation context and SQL.

    The agent follows a specific workflow:
    1. First queries Alation for table schema information using the context tool
    2. Then formulates SQL to look up customer information by email or other identifiers
    3. Executes the SQL against the database
    4. Returns structured customer information

    This pattern demonstrates how Alation metadata can directly inform database queries.
    """

    # Initialize the LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    if USE_MOCK_DATA == "true":
        from mocks.alation_mocks import mock_alation_context

        def mock_alation_wrapper(question: str):
            return mock_alation_context(question, signature=CUSTOMER_PROFILE_SIGNATURE)

        tools = [
            Tool(
                name="alation_context",
                description="Mocked Alation catalog context",
                func=mock_alation_wrapper,
            )
        ]
    else:
        # Get Alation tools and add SQL execution tool
        tools = get_alation_tools()

    # Add SQL execution tool - making it generic
    sql_tool = Tool(
        name="execute_sql",
        description="""Execute SQL queries against the customer database.
        Input should be a valid SQL query string.
        Returns the query results as a JSON object.

        Example:
        SELECT * FROM table_name WHERE column = 'value'
        """,
        func=execute_sql,
    )

    tools.append(sql_tool)

    # Define the system prompt for the agent
    system_prompt = """You are a customer identification agent for a retail company.
Your job is to identify customers based on their email or details in their query.

Follow this exact process:
1. FIRST, use the alation_context tool to get information about the vw_customer_profile view
    - Ask about the columns and structure of vw_customer_profile table

2. NEXT, based on the Alation context, create an appropriate SQL query to find the customer
   - Primarily search by email if available
   - Fall back to other identifiers (name, phone) if needed

3. THEN, execute the SQL query using the execute_sql tool

4. FINALLY, organize and return the customer information in a clear JSON format

If you cannot identify the customer with confidence, clearly state this."""

    # Create the agent using the new pattern
    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
    return agent


def user_identification_node(state: CustomerState) -> CustomerState:
    """Process the state through the identification agent with Alation context and SQL."""
    agent = create_identification_agent()

    # Create the user message with all the context
    user_message = f"""Customer query: {state["query"]}
Customer email: {state.get("email", "")}

Please identify the customer using the process you've been instructed to follow."""

    # Run the agent with messages format
    result = agent.invoke({"messages": [("user", user_message)]})

    # Extract customer information from the agent's output
    try:
        # Get the final message content
        if hasattr(result, 'get') and 'messages' in result:
            # Extract the final assistant message
            messages = result.get('messages', [])
            if messages:
                final_message = messages[-1]
                if hasattr(final_message, 'content'):
                    output = final_message.content
                else:
                    output = str(final_message)
            else:
                output = str(result)
        else:
            output = str(result)

        # Parse the agent output for customer information
        customer_info = extract_customer_info(output)

        # Update state with customer info
        state["customer_info"] = customer_info

        # Check if we failed to identify the customer
        if not customer_info or not customer_info.get("id"):
            state["agent_notes"] = state.get("agent_notes", []) + [
                "Failed to identify customer. Proceed with limited functionality."
            ]
    except Exception as e:
        state["agent_notes"] = state.get("agent_notes", []) + [
            f"Error processing customer identification: {str(e)}"
        ]
        state["customer_info"] = {}

    # Update phase
    state["agent_notes"] = state.get("agent_notes", []) + [
        f"Identification complete: {output if 'output' in locals() else 'No output'}"
    ]
    state["current_phase"] = "context"

    return state


def extract_customer_info(agent_output: str) -> Dict[str, Any]:
    """
    Extract structured customer information from the agent's output.
    """
    # Start with empty info
    customer_info = {}

    # Try to find JSON blocks in the output
    try:
        # Look for JSON structure in the output
        start_idx = agent_output.find("{")
        end_idx = agent_output.rfind("}")

        if start_idx >= 0 and end_idx > start_idx:
            json_str = agent_output[start_idx : end_idx + 1]
            customer_info = json.loads(json_str)
            return customer_info
    except Exception:
        pass

    return customer_info
