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

from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    ServiceAccountAuthParams,
)
from alation_ai_agent_sdk.api import AlationAPIError


def print_json(data: Dict[str, Any]) -> None:
    """Helper function to pretty-print JSON."""
    print(json.dumps(data, indent=2))


def initialize_sdk(base_url: str, auth_method: str) -> AlationAIAgentSDK:
    """Initialize the Alation AI Agent SDK based on the authentication method."""
    if auth_method == "service_account":
        client_id = os.getenv("ALATION_CLIENT_ID")
        client_secret = os.getenv("ALATION_CLIENT_SECRET")

        if not all([client_id, client_secret]):
            raise ValueError(
                "Missing required environment variables for service account authentication. Please set ALATION_CLIENT_ID and ALATION_CLIENT_SECRET."
            )

        return AlationAIAgentSDK(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=ServiceAccountAuthParams(
                client_id=client_id, client_secret=client_secret
            ),
        )

    else:
        raise ValueError(f"Unsupported ALATION_AUTH_METHOD: {auth_method}")


def main() -> None:
    # Load credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    auth_method = os.getenv("ALATION_AUTH_METHOD")

    # Validate environment variables
    if not base_url or not auth_method:
        print("Error: Missing required environment variables.")
        print("Please set ALATION_BASE_URL and ALATION_AUTH_METHOD.")
        return

    try:
        print(f"Initializing Alation AI Agent SDK with {auth_method} authentication...")
        sdk = initialize_sdk(base_url, auth_method)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Example 1: Basic query without signature
    print("\n=== Example 1: Basic Query ===")
    print(
        "Query: Fetch detail about customer (no signature- by default fetches multiple objects)"
    )

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
                "fields": {"tag_ids": [2]}
            },  # Replace with actual tag ID
        }
    }

    try:
        response = sdk.get_context(
            "Can you explain transactions table?", signature=table_signature
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
                "columns": {"fields": ["name", "title", "data_type", "description"]}
            },
        }
    }

    try:
        response = sdk.get_context(
            "Tell me about the customer_profile table", signature=detailed_signature
        )
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    # Example 4: Query for documentation
    print("\n=== Example 4: Query for Documentation ===")
    print("Query: Fetch documentation on loan term and loan type")

    # Define a signature for documentation
    docs_signature = {"documentation": {"fields_required": ["title", "content", "url"]}}

    try:
        response = sdk.get_context(
            "What is the difference between loan type and loan term",
            signature=docs_signature,
        )
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    # Example 5: Bulk retrieval of objects
    print("\n=== Example 5: Bulk retrieval of objects ===")
    print("Query: Get all Endorsed Tables in a data source")

    # Define a signature that includes column information
    detailed_signature = {
        "table": {
            "fields_required": ["name", "title", "description", "url"],
            "search_filters": {"flags": ["Endorsement"], "fields": {"ds": [1]}},
            "limit": 20,
        }
    }
    try:
        response = sdk.get_bulk_objects(signature=detailed_signature)
        print_json(response)
    except AlationAPIError as e:
        print(f"API Error: {e}")
        return

    print("\nAll examples completed successfully!")


if __name__ == "__main__":
    main()
