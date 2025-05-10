# agents/customer_context.py
"""
Context Aggregation Agent: intelligently selects and fetches tables based on query relevance.
"""
import json
import ast
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from schemas import CustomerState, CUSTOMER_DATA_SIGNATURE
from config import LLM_MODEL, USE_MOCK_DATA
from tools import execute_sql, get_alation_tools


# In future this should be fetched from alation using tools similar to alation_context tool.
# Tool should fetch all the tables relevant to use case.
# Signature should be used to scope the views/tables.
def get_catalog_tables():
    """
    Get all relevant tables/views needed for this agent
    """
    return [
        {"name": "vw_customer_purchase_history", "title": "Customer Purchase History View"},
        {"name": "vw_customer_membership_benefits", "title": "Customer Membership Benefits View"},
        {"name": "vw_customer_product_warranties", "title": "Customer Product Warranties View"}
    ]


def select_relevant_tables(available_tables, query):
    """Use LLM to determine which tables are relevant to the question."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    # Create prompt - making it more general without specific table mentions
    prompt = f"""
    Based on this question: "{query}"

    Identify the most relevant tables from this list:
    {available_tables}

    Analyze the query to determine which information would be most helpful to answer it.

    Return ONLY a list of table names, e.g.: ["table1", "table2"]
    ONLY include tables that are DIRECTLY RELEVANT to answering the query.
    """

    # Get LLM response
    response = llm.invoke(prompt)

    try:
        # Parse LLM response
        selected_tables = ast.literal_eval(response.content)
        if not isinstance(selected_tables, list):
            raise ValueError("Response is not a list")

        # Ensure relevant tables are always considered
        available_table_names = [table.get("name") for table in available_tables]

        # Validate that all selected tables exist in available tables
        validated_tables = [table for table in selected_tables if table in available_table_names]

        # Fallback: If no tables were selected or validation removed all selections
        if not validated_tables and "vw_customer_purchase_history" in available_table_names:
            validated_tables.append("vw_customer_purchase_history")

        return validated_tables
    except Exception:
        # Fallback if needed. You can also raise an error here.
        default_tables = ["vw_customer_purchase_history"]
        return default_tables


def create_context_agent(selected_table_names):
    """Create an agent to query the selected tables."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    # Format table names as a comma-separated list
    tables_list = ", ".join(selected_table_names)

    # Get Alation context tool and SQL execution tool
    if USE_MOCK_DATA == 'true':
        from mocks.alation_mocks import mock_alation_context
        from langchain.tools import Tool

        def mock_alation_wrapper(question: str):
            return mock_alation_context(question, signature=CUSTOMER_DATA_SIGNATURE)

        tools = [Tool(
            name="alation_context",
            description="Mocked Alation catalog context",
            func=mock_alation_wrapper
        )]
    else:
        # Get Alation tools
        tools = get_alation_tools()

    # Add SQL execution tool
    sql_tool = Tool(
        name="execute_sql",
        description="Execute SQL queries against the database. Returns JSON results.",
        func=execute_sql
    )

    tools.append(sql_tool)

    # Create a simpler system message that avoids template issues
    system_message = f"""You are a database query agent. Your job:

1. FIRST, use the alation_context tool to get information for all the relevant table structures.
    - IMPORTANT: When calling the alation_context tool, you must pass TWO parameters:
         1) The question string: "What are the columns and structure of {tables_list}?"
         2) The signature object that was provided to you
    - DO NOT modify the signature or include it in the question string

2. THEN, for each of these tables: {tables_list}
   - Create an SQL query that selects all data for a specific customer
   - The query format should be: SELECT * FROM table_name WHERE customer_id = 'customer_id_value'
   - Use the exact table name and the customer ID provided by the user

3. NEXT, execute each query using the execute_sql tool

4. FINALLY, compile all the results into a structured response.
   Return the results as a clean JSON object mapping table names to their query results.
   Do not include any explanatory text before or after the JSON - just return the raw JSON data.
"""

    # Create the prompt with direct string instead of using formatting
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Customer ID: {customer_id}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    return AgentExecutor(agent=agent, tools=tools, verbose=False)


# This Context Aggregation Agent implements a multi-step intelligence process to:
# 1. Identify potentially relevant tables from the Alation catalog based on the user query
# 2. Use an LLM to intelligently select the most contextually appropriate tables
# 3. Query each selected table for the specific customer data
# 4. Compile all retrieved data into a cohesive context package for decision-making
#
# While this functionality could be implemented procedurally, the agent architecture
# provides flexibility and demonstrates how to build contextual intelligence into
# a customer service workflow. This implementation can be extended with additional
# data sources and more sophisticated relevance-matching algorithms.
def customer_context_node(state: CustomerState) -> CustomerState:
    """Determine which tables to query based on context and fetch data."""
    # Get customer ID
    customer_id = state.get("customer_info", {}).get("customer_id") or state.get("customer_info", {}).get("id")
    if not customer_id:
        state.setdefault("agent_notes", []).append("No customer_id; skipping context gathering.")
        state["context_data"] = {}
        state["current_phase"] = "eligibility"
        return state

    # Step 1: Get available tables.
    # In future this should be able to get all objects from alation directly.
    # You should be also able to provide a signature to specify which objects and fields you want.
    all_tables = get_catalog_tables()

    # Step 2: Use LLM to select relevant tables based on the query
    query = state.get("query", "")
    selected_table_names = select_relevant_tables(all_tables, query)

    if not selected_table_names:
        state.setdefault("agent_notes", []).append("No relevant tables selected; skipping context gathering.")
        state["context_data"] = {}
        state["current_phase"] = "eligibility"
        return state

    # Step 3: Create and execute context agent with the selected table names
    agent = create_context_agent(selected_table_names)

    # Prepare input
    input_data = {
        "customer_id": customer_id
    }

    # Run the agent
    result = agent.invoke(input_data)

    # Store into state
    state.setdefault("context_data", {})

    # Process the agent result
    output = result.get('output', '')

    try:
        # Try to parse JSON directly from the output
        if isinstance(output, str):
            # Remove any text before or after the JSON
            import re
            json_match = re.search(r'({.*})', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                parsed_result = json.loads(json_str)
                state["context_data"] = parsed_result
            else:
                raise ValueError("No JSON found in output")
        elif isinstance(output, dict):
            state["context_data"] = output
        else:
            raise ValueError(f"Unexpected output type: {type(output)}")
    except Exception as e:
        # Fallback for unexpected format
        state.setdefault("agent_notes", []).append(
            f"Error parsing context data: {str(e)}. Using empty data."
        )
        for table_name in selected_table_names:
            state["context_data"][table_name] = []

    state.setdefault("agent_notes", []).append(
        f"Fetched data from tables: {', '.join(selected_table_names)}"
    )

    # Move to next phase
    state["current_phase"] = "eligibility"
    return state
