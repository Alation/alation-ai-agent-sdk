"""
Main entry point for the minimal multi-agent customer service system.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END, START

from schemas import CustomerState
from agents.user_identification import user_identification_node as identification_node
from agents.customer_context import customer_context_node as context_node
from agents.eligibility import eligibility_node  # If you have this combined agent instead


def build_customer_service_graph():
    """Build and return the multi-agent workflow as a graph."""
    # Initialize the state graph
    workflow = StateGraph(CustomerState)

    # Add nodes for each specialized agent
    workflow.add_node("identification", identification_node)
    workflow.add_node("context", context_node)
    workflow.add_node("eligibility", eligibility_node)

    # Add the START edge
    workflow.add_edge(START, "identification")

    # Add edges for the standard workflow
    workflow.add_edge("identification", "context")
    workflow.add_edge("context", "eligibility")
    workflow.add_edge("eligibility", END)

    # Return the compiled workflow
    return workflow.compile()


def handle_customer_request(
        customer_query: str,
        user_email: str,
        debug_mode: bool = False
) -> Dict[str, Any]:
    """
    Process a customer service request through the multi-agent workflow.

    Args:
        customer_query: The customer's question or request
        user_email: Optional email to help identify the customer
        debug_mode: Whether to include debug information in the response

    Returns:
        Dict containing the final response and optionally debug information
    """
    # Build the multi-agent graph
    customer_service_graph = build_customer_service_graph()

    # Prepare initial state
    initial_state = CustomerState(
        query=customer_query,
        email=user_email,
        agent_notes=[],
        current_phase="start",
        requires_human=False
    )

    # Execute the multi-agent workflow
    result = customer_service_graph.invoke(initial_state)

    # Return the result
    if debug_mode:
        return {
            "response": result.get("final_response", "No response generated"),
            "state": result
        }
    else:
        return {
            "response": result.get("final_response", "No response generated")
        }


def print_banner():
    """Print a welcome banner for the application"""
    print("\n" + "=" * 80)
    print(" " * 20 + "RETURN ELIGIBILITY ASSISTANT" + " " * 20)
    print("=" * 80 + "\n")


if __name__ == "__main__":

    email = "jane.doe@example.com"
    # Print welcome banner
    print_banner()

    # Get customer query from terminal
    query = input("What would you like to return? Please describe your request: ")
    print("\nProcessing your request. This may take a moment...\n")

    result = handle_customer_request(query, email, debug_mode=True)

    print("\n=== CUSTOMER SERVICE RESPONSE ===\n")
    print(result["response"])

    if result.get("state"):
        print("\n=== DEBUG INFORMATION ===\n")
        print(f"Customer: {result['state'].get('customer_info', {})}")
        print(f"Context: {result['state'].get('context_data', {})}")
        print(f"Eligibility: {result['state'].get('eligibility_status', 'unknown')}")
        print(f"Required Human: {result['state'].get('requires_human', False)}")

        if result['state'].get('agent_notes'):
            print("\nAgent Notes:")
            for note in result['state'].get('agent_notes', []):
                print(f"- {note}")
