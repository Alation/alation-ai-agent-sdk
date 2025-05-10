"""
Basic usage examples for the Alation AI Agent SDK.

This script demonstrates:
1. Initializing the SDK
2. Making basic context queries
3. Using signatures to customize responses
4. Error handling

Usage:
    python basic_usage.py
"""

import os
import json
from typing import Dict, Any

from alation_ai_agent_sdk import AlationAIAgentSDK
from alation_ai_agent_sdk.api import AlationAPIError


def print_json(data: Dict[str, Any]) -> None:
    """Helper function to pretty-print JSON."""
    print(json.dumps(data, indent=2))


def main() -> None:
    # Load credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    user_id_str = os.getenv("ALATION_USER_ID")
    refresh_token = os.getenv("ALATION_REFRESH_TOKEN")

    # Validate environment variables
    if not all([base_url, user_id_str, refresh_token]):
        print("Error: Missing required environment variables.")
        print("Please set ALATION_BASE_URL, ALATION_USER_ID, and ALATION_REFRESH_TOKEN.")
        return

    try:
        user_id = int(user_id_str)
    except ValueError:
        print(f"Error: ALATION_USER_ID must be an integer, got: {user_id_str}")
        return

    # Initialize the SDK
    print("Initializing Alation AI Agent SDK...")
    sdk = AlationAIAgentSDK(
        base_url=base_url,
        user_id=user_id,
        refresh_token=refresh_token
    )

    # Example 1: Basic query without signature
    print("\n=== Example 1: Basic Query ===")
    print("Query: Fetch detail about customer (no signature- by default fetches multiple objects)")

    try:
        response = sdk.get_context("What tables contain customer information?")
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    # Example 2: Query with a basic table signature
    print("\n=== Example 2: Query with Table Signature ===")
    print("Query: Fetch transactions table?")

    # Define a signature that requests specific table fields.
    #
    # This example assumes there ia a common tag across the relevant tables
    # and uses it here to restrict the search to only those tables.
    table_signature = {
        "table": {
            "fields_required": ["name", "title", "description", "url"],
            "fields_optional": ["common_joins", "common_filters"],
            "search_filters": {
                "fields": {
                    "tag_ids": [2]  # Replace with actual tag ID
                }
            }
        }
    }

    try:
        response = sdk.get_context(
            "Can you explain transactions table?",
            signature=table_signature
        )
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    # Example 3: Query with table and column details
    print("\n=== Example 3: Query with Table and Column Details ===")
    print("Query: Fetch customer_profile table")

    # Define a signature that includes column information
    detailed_signature = {
        "table": {
            "fields_required": ["name", "title", "description", "url", "columns"],
            "child_objects": {
                "columns": {
                    "fields": ["name", "title", "data_type", "description"]
                }
            }
        }
    }

    try:
        response = sdk.get_context(
            "Tell me about the customer_profile table",
            signature=detailed_signature
        )
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    # Example 4: Query for documentation
    print("\n=== Example 4: Query for Documentation ===")
    print("Query: Fetch documentation on loan term and loan type")

    # Define a signature for documentation
    docs_signature = {
        "documentation": {
            "fields_required": ["title", "content", "url"]
        }
    }

    try:
        response = sdk.get_context(
            "What is the difference between loan type and loan term",
            signature=docs_signature
        )
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    main()
