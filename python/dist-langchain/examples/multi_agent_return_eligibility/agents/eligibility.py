"""
Eligibility agent that determines return eligibility by retrieving policies and making decisions.
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from schemas import CustomerState, POLICY_SIGNATURE
from tools import get_alation_tools
from config import LLM_MODEL, USE_MOCK_DATA



def create_eligibility_agent() -> AgentExecutor:
    """Create an agent for determining return eligibility."""
    # Initialize the LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    if USE_MOCK_DATA == "true":
        from mocks.alation_mocks import mock_alation_context
        from langchain.tools import Tool

        def mock_alation_wrapper(question: str):
            return mock_alation_context(question, signature=POLICY_SIGNATURE)

        tools = [
            Tool(
                name="alation_context",
                description="Mocked Alation catalog context",
                func=mock_alation_wrapper
            )
        ]
    else:
        # Get Alation tools
        tools = get_alation_tools()

    # Define the agent prompt with response generation
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a return eligibility agent for a retail company.
        TODAY'S DATE is June 20, 2023. Use this exact date for all eligibility calculations.

        Your job is to:

        1. FIRST, identify the product category and specific product name from the purchase information

        2. THEN, use the alation_context tool to retrieve the relevant return policy:
            - IMPORTANT: When calling the alation_context tool, you must pass TWO parameters:
                 1) The question string: "Fetch policy for [specific product category]"
                 2) The signature object that was provided to you
           - DO NOT modify the signature or include it in the question string

        3. CAREFULLY read the policy to determine:
           - The standard return window for this SPECIFIC product type
           - Any special conditions (opened vs unopened, etc.)
           - Any membership tier benefits that extend the window
           - The high-value threshold requiring approval

        4. CALCULATE how many days have passed since purchase date, using today's date (June 20, 2023)

        5. ANALYZE the customer's situation against the policy:
           - Days since purchase compared to the applicable return window
           - Membership benefits that extend the standard window
           - Product condition if mentioned
           - Purchase value compared to high-value threshold
           - Note: Warranty service is separate from return eligibility

        6. DECIDE if the return is:
           - "eligible" (within policy, no special handling)
           - "eligible_with_approval" (requires manager approval)
           - "ineligible" (outside policy)

        7. GENERATE a friendly customer response that:
           - Addresses the customer by name
           - Clearly states if the return is eligible or not
           - Explains why (referencing the specific policy details)
           - If eligible: Provides clear next steps for the return process
           - If ineligible: Offers alternative solutions (e.g., warranty service) if applicable
           - Is concise and empathetic

        IMPORTANT: Respond with a JSON object containing:
        {{
          "eligibility_status": "eligible|eligible_with_approval|ineligible",
          "requires_human": true|false,
          "policy_info": {{
            "return_window_days": [number],
            "high_value_threshold": [number],
            "reason": "[detailed explanation]",
            "applied_policy": "[relevant policy section]",
            "product_name": "[specific product being returned]"
          }},
          "customer_response": "[complete customer-friendly response text]"
        }}
        """),
        ("human", """
        Customer query: {input}
        Customer information: {customer_info}
        Purchase information: {purchase_info}
        Signature: {signature}
        """),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_functions_agent(llm=llm, prompt=prompt, tools=tools)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def eligibility_node(state: CustomerState) -> CustomerState:
    """Process the state through the eligibility agent."""
    # Skip if no purchase info is available
    if not state.get("context_data"):
        state["eligibility_status"] = "unknown"
        state["requires_human"] = True
        state["agent_notes"] = state.get("agent_notes", []) + [
            "Cannot determine eligibility - missing purchase information"]
        state["current_phase"] = "complete"
        return state

    agent = create_eligibility_agent()

    # Prepare input
    input_data = {
        "input": state["query"],
        "customer_info": state.get("customer_info", {}),
        "purchase_info": state["context_data"],
        "signature": POLICY_SIGNATURE
    }

    # Run the agent with try/except
    try:
        result = agent.invoke(input_data)

        # Extract the agent's output
        output = result.get('output', '')
        import json
        import re

        # Try to find JSON in the output
        json_match = re.search(r'({.*})', output, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                decision_data = json.loads(json_str)

                # Update state with decision data
                state["eligibility_status"] = decision_data.get("eligibility_status", "unknown")
                state["requires_human"] = decision_data.get("requires_human", True)
                state["policy_info"] = decision_data.get("policy_info", {})

                # Use the generated customer response
                if "customer_response" in decision_data:
                    state["final_response"] = decision_data["customer_response"]
                else:
                    # Fallback if no customer response was generated
                    state[
                        "final_response"] = f"We've evaluated your return request. Your item is {state['eligibility_status']} for return."

            except json.JSONDecodeError:
                state["eligibility_status"] = "unknown"
                state["requires_human"] = True
                state["policy_info"] = {"reason": "Could not parse eligibility decision"}
                state[
                    "final_response"] = "We're having trouble processing your return request. Please contact customer service."
        else:
            # Fallback if no JSON found
            state["eligibility_status"] = "unknown"
            state["requires_human"] = True
            state["policy_info"] = {"reason": "Could not parse agent decision"}
            state[
                "final_response"] = "We're having trouble processing your return request. Please contact customer service."

    except Exception as e:
        state["eligibility_status"] = "unknown"
        state["requires_human"] = True
        state["agent_notes"] = state.get("agent_notes", []) + [f"Error in eligibility determination: {str(e)}"]
        state["policy_info"] = {"reason": f"Error: {str(e)}"}
        state[
            "final_response"] = "We're having trouble processing your return request. Please contact customer service."

    # Add agent response to notes if available
    if 'result' in locals() and 'output' in result:
        state["agent_notes"] = state.get("agent_notes", []) + [f"Eligibility: {result['output']}"]

    state["current_phase"] = "complete"
    return state
