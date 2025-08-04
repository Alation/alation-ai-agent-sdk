"""
Data Product Creation Example

This demonstrates how to use the Alation AI Agent SDK to automatically create
data products by gathering context from your catalog and generating YAML specifications.

Simplified 3-step approach:
1. Fetch context from catalog using bulk retrieval
2. Get schema instructions from your Alation instance
3. Generate data product YAML using OpenAI GPT-4

Requirements:
- Alation AI Agent SDK
- OpenAI API key

Usage:
    python data_product_generation.py --domain_ids "191,192" --product_name "Sales Analytics"
    python data_product_generation.py --domain_ids "191" --product_name "Customer Analytics"

Environment variables:
    ALATION_BASE_URL: URL of your Alation instance
    ALATION_USER_ID: Your Alation user ID (for user_account auth)
    ALATION_REFRESH_TOKEN: Your Alation refresh token (for user_account auth)
    ALATION_CLIENT_ID: Your Alation client ID (for service_account auth)
    ALATION_CLIENT_SECRET: Your Alation client secret (for service_account auth)
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
import argparse
from typing import Dict, Any, List

import openai
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams
from alation_ai_agent_sdk.api import AlationAPIError


def generate_data_product(
        sdk: AlationAIAgentSDK,
        domain_ids: List[str],
        product_name: str,
        openai_client: openai.OpenAI
) -> str:
    """
    Create data product in 3 simple steps.

    Args:
        sdk: Initialized Alation SDK
        domain_ids: List of domain IDs to filter by (e.g., ["191", "192"])
                   Note: This is just one example of filtering. You could modify this
                   function to use any other search criteria supported by Alation:
                   - ds: [123] for data source IDs
                   - tag_ids: [456] for tag IDs
                   - flags: ["Endorsement"] for endorsement flags
                   - Any combination of the above
        product_name: Name for the data product (e.g., "Sales Analytics")

    Returns:
        Generated YAML string for Alation Data Product
    """

    print(f"Creating '{product_name}' data product...")
    print(f"Filtering by domain IDs: {domain_ids}")

    # STEP 1: Fetch context (tables + SQL patterns in one go)
    print("Step 1: Fetching catalog context...")

    try:
        # Get tables with relationships and columns
        # Note: You can modify the search_filters below to use any supported criteria:
        # - "ds": [123, 456] for data sources
        # - "tag_ids": [789] for tags
        # - "flags": ["Endorsement"] for endorsed content
        # - Any combination of filters
        # You could also add filters, sample values too if needed. We have kept it simple here.
        tables = sdk.get_bulk_objects({
            "table": {
                "fields_required": ["name", "description", "common_joins", "columns"],
                "search_filters": {
                    "fields": {
                        "domain_ids": domain_ids  # This could be any other search criteria
                    }
                },
                "child_objects": {
                    "columns": {"fields": ["name", "data_type", "description"]}
                },
                "limit": 15
            }
        })
    except AlationAPIError as e:
        print(f"Warning: Error fetching tables: {e}")
        tables = {}

    try:
        # Get SQL patterns from the same scope
        queries = sdk.get_bulk_objects({
            "query": {
                "fields_required": ["title", "description", "content"],
                "search_filters": {
                    "fields": {
                        "domain_ids": domain_ids  # This could be any other search criteria
                    }
                },
                "limit": 5
            }
        })
    except AlationAPIError as e:
        print(f"Warning: Error fetching queries: {e}")
        queries = {}

    # STEP 2: Get schema instructions from your Alation instance
    print("Step 2: Getting latest schema instructions...")
    try:
        instructions = sdk.generate_data_product()
        print(instructions)
    except (AttributeError, AlationAPIError) as e:
        print(f"Warning: Could not fetch schema from Alation instance: {e}")

    # STEP 3: Generate YAML using AI model
    print("Step 3: Generating data product YAML...")

    # Create context for AI model
    context_text = _format_context(tables, queries, product_name)

    prompt = f"""
{instructions}

{context_text}

Generate the YAML for "{product_name}" data product.
"""

    # TODO: Replace with your AI model call
    yaml_result = _call_ai_model(prompt, openai_client)

    print("Data product created!")
    return yaml_result


def _format_context(tables_data: Dict[str, Any], queries_data: Dict[str, Any], product_name: str) -> str:
    """Format the catalog context for the AI model."""

    context = [f"Create data product: {product_name}"]

    # Add available tables
    tables = tables_data.get('relevant_tables', [])
    if tables:
        context.append(f"\nFound {len(tables)} tables:")
        for table in tables:
            name = table.get('name', '')
            desc = table.get('description', '')
            context.append(f"- {name}: {desc}")

            # Add key columns for context
            columns = table.get('columns', [])
            if columns:
                col_list = []
                for col in columns:
                    col_name = col.get('name', '')
                    col_type = col.get('data_type', '') or col.get('type', '') or col.get('datatype', '')
                    if col_type:
                        col_list.append(f"{col_name} ({col_type})")
                    else:
                        col_list.append(col_name)
                context.append(f"  All columns: {', '.join(col_list)}")

            # Add relationship information if available
            joins = table.get('common_joins', [])
            if joins:
                context.append(f"  Relationships: {len(joins)} common joins")

    # Add SQL patterns for business context
    queries = queries_data.get('queries', [])
    if queries:
        context.append(f"\nFound {len(queries)} SQL queries showing business patterns:")

        # Add example query titles for business context
        for query in queries:
            title = query.get('title', 'Untitled Query')
            context.append(f"- {title}")

    return '\n'.join(context)


def _call_ai_model(prompt: str, openai_client: openai.OpenAI) -> str:
    """
    Call OpenAI GPT-4 to generate the YAML.

    Args:
        prompt: The complete prompt including schema and context
        openai_client: Initialized OpenAI client

    Returns:
        Generated YAML string for Alation Data Product
    """

    print(f"Sending prompt to OpenAI GPT-4o ({len(prompt)} characters)")

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating Alation Data Product YAML specifications. Follow the provided schema exactly and only use information provided by the user. Never hallucinate or add realistic-looking data not provided."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Lower temperature for more consistent, focused output
            max_tokens=2000  # Increase it to allow for longer YAML responses
        )

        yaml_content = response.choices[0].message.content.strip()
        print("Successfully generated YAML from OpenAI")
        return yaml_content

    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return f"# Error generating YAML: OpenAI API Error - {e}"

    except openai.RateLimitError as e:
        print(f"OpenAI Rate Limit Error: {e}")
        return f"# Error generating YAML: Rate limit exceeded - {e}"

    except Exception as e:
        print(f"Unexpected error calling OpenAI: {e}")
        return f"# Error generating YAML: Unexpected error - {e}"


def initialize_sdk(auth_method: str) -> AlationAIAgentSDK:
    """Initialize the Alation SDK based on authentication method."""

    base_url = os.getenv("ALATION_BASE_URL")
    if not base_url:
        raise ValueError("ALATION_BASE_URL environment variable is required")

    if auth_method == "user_account":
        user_id_str = os.getenv("ALATION_USER_ID")
        refresh_token = os.getenv("ALATION_REFRESH_TOKEN")

        if not all([user_id_str, refresh_token]):
            raise ValueError("ALATION_USER_ID and ALATION_REFRESH_TOKEN required for user_account auth")

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise ValueError("ALATION_USER_ID must be an integer")

        return AlationAIAgentSDK(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=UserAccountAuthParams(user_id, refresh_token)
        )

    elif auth_method == "service_account":
        client_id = os.getenv("ALATION_CLIENT_ID")
        client_secret = os.getenv("ALATION_CLIENT_SECRET")

        if not all([client_id, client_secret]):
            raise ValueError("ALATION_CLIENT_ID and ALATION_CLIENT_SECRET required for service_account auth")

        return AlationAIAgentSDK(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=ServiceAccountAuthParams(client_id, client_secret)
        )

    else:
        raise ValueError("auth_method must be 'user_account' or 'service_account'")


def main():
    """Main function - simplified to use only domain IDs."""

    parser = argparse.ArgumentParser(description="Create Alation Data Product from catalog context")
    parser.add_argument("--domain_ids", required=True,
                        help="Comma-separated domain IDs to filter by (example: '191,192' or just '191')")
    parser.add_argument("--product_name", required=True, help="Name for the data product")
    parser.add_argument("--auth_method", default="user_account",
                        choices=["user_account", "service_account"],
                        help="Authentication method")

    args = parser.parse_args()

    # Parse domain IDs from comma-separated string
    try:
        domain_ids = [id.strip() for id in args.domain_ids.split(',') if id.strip()]
        if not domain_ids:
            raise ValueError("No valid domain IDs provided")
    except Exception as e:
        print(f" Error parsing domain IDs: {e}")
        print("   Example: --domain_ids '191,192' or --domain_ids '191'")
        return

    print(f"Using domain IDs: {domain_ids}")

    try:
        # Initialize SDK
        sdk = initialize_sdk(args.auth_method)

        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                "Missing OpenAI API key. Please set OPENAI_API_KEY environment variable."
            )

        openai_client = openai.OpenAI(api_key=openai_api_key)
        print("OpenAI client initialized")

        # Create data product
        yaml_result = generate_data_product(sdk, domain_ids, args.product_name, openai_client)

        print("\n" + "=" * 60)
        print("GENERATED DATA PRODUCT YAML:")
        print("=" * 60)
        print(yaml_result)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
