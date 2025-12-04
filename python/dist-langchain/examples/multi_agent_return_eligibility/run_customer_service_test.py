"""
End-to-End Test Script for Return Eligibility Agent

This script tests the complete workflow of the multi-agent system for determining
return eligibility. It runs through multiple test cases to validate different scenarios.
"""

import json

from schemas import CustomerState
from agents.user_identification import (
    create_identification_agent,
    extract_customer_info,
)
from agents.customer_context import customer_context_node
from agents.eligibility import eligibility_node


def format_section_header(title):
    """Format a section header for better readability."""
    width = 80
    padding = (width - len(title) - 2) // 2
    return (
        "\n"
        + "=" * width
        + "\n"
        + " " * padding
        + title
        + " " * padding
        + "\n"
        + "=" * width
    )


def run_test_case(
    case_name, query, email="jane.doe@example.com", expected_eligibility=None
):
    """
    Run a complete test case through all phases of the agent workflow.

    Args:
        case_name: Name/description of the test case
        query: The customer query to process
        email: Customer email for identification
        expected_eligibility: Expected eligibility result (for validation)
    """
    print(format_section_header(f"TEST CASE: {case_name}"))
    print(f"Query: '{query}'")
    print(f"Customer Email: {email}")
    print()

    # === Phase 1: Identification ===
    print("Phase 1: IDENTIFICATION")
    print("-" * 50)

    agent = create_identification_agent()
    user_message = f"""Customer query: {query}
Customer email: {email}

Please identify the customer using the process you've been instructed to follow."""
    result = agent.invoke({"messages": [("user", user_message)]})

    # Extract customer info - handle new result format
    try:
        if hasattr(result, "get") and "messages" in result:
            # Extract the final assistant message
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                if hasattr(final_message, "content"):
                    output = final_message.content
                else:
                    output = str(final_message)
            else:
                output = str(result)
        else:
            output = str(result)
    except Exception:
        output = str(result)

    customer_info = extract_customer_info(output)
    print("\nExtracted Customer Info:")
    print(json.dumps(customer_info, indent=2))

    # Build state for next phase
    state = CustomerState(
        query=query,
        email=email,
        customer_info=customer_info,
        agent_notes=[],
        current_phase="identification",
        requires_human=False,
    )

    # === Phase 2: Context Gathering ===
    print("\nPhase 2: CONTEXT GATHERING")
    print("-" * 50)

    state = customer_context_node(state)

    context_tables = state.get("agent_notes", {})
    print(f"\nRetrieved data from tables: {context_tables}")

    # For brevity, we'll just show table names, not full data
    # In a real test, you might want to inspect the full data for certain cases

    # === Phase 3: Eligibility Determination ===
    print("\nPhase 3: ELIGIBILITY DETERMINATION")
    print("-" * 50)

    state = eligibility_node(state)

    eligibility_status = state.get("eligibility_status")
    requires_human = state.get("requires_human")

    print(f"Eligibility Status: {eligibility_status}")
    print(f"Requires Human: {requires_human}")

    if "policy_info" in state:
        print("\nPolicy Applied:")
        policy_info = state.get("policy_info", {})
        for key, value in policy_info.items():
            print(f"  {key}: {value}")

    # === Final Response ===
    print("\nFINAL RESPONSE:")
    print("-" * 50)
    print(state.get("final_response", "No response generated").strip())

    # === Validation ===
    if expected_eligibility:
        print("\nVALIDATION:")
        print("-" * 50)
        actual = state.get("eligibility_status", "unknown")
        match = actual == expected_eligibility
        print(f"Expected: {expected_eligibility}, Actual: {actual}, Match: {match}")

    return state


def run_all_tests():
    """Run all test cases."""

    # Standard return within window
    run_test_case(
        "Standard Return Within Window",
        "I want to return the headphones I bought last week.",
        expected_eligibility="eligible",
    )

    # Return with gold membership benefits
    run_test_case(
        "Return With Extended Gold Membership Window",
        "I bought headphones 40 days ago. Can I return them with my Gold membership?",
        expected_eligibility="eligible",
    )

    # Return outside window but with warranty
    run_test_case(
        "Return Outside Window But Under Warranty",
        "My wireless earbuds I bought in April are having issues with the sound. Can I return them?",
        expected_eligibility="ineligible",  # Outside return window but under warranty
    )

    # High-value purchase requiring approval
    run_test_case(
        "High-Value Purchase Requiring Approval",
        "I need to return the Smart TV I purchased last month.",
        expected_eligibility="eligible_with_approval",  # Should be eligible but require human approval
    )

    # Ineligible return (outside window without warranty)
    run_test_case(
        "Ineligible Return - Outside Window",
        "Can I return a laptop sleeve I bought 6 months ago?",
        expected_eligibility="ineligible",
    )

    # Multiple items mentioned (should focus on one)
    run_test_case(
        "Return Request With Multiple Items",
        "I want to return the headphones and laptop sleeve I bought. Are they still covered?",
        expected_eligibility="eligible",  # Should focus on the headphones which are eligible
    )

    # Different user (John Smith - Silver member)
    run_test_case(
        "Different Customer - Silver Membership",
        "I need to return my Bluetooth speaker. Does my Silver membership help?",
        email="john.smith@example.com",
        expected_eligibility="eligible",
    )


if __name__ == "__main__":
    run_all_tests()
