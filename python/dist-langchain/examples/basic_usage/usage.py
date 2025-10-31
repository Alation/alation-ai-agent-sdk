import os
import json

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from alation_ai_agent_langchain import (
    AlationAIAgentSDK,
    ServiceAccountAuthParams,
    get_langchain_tools,
)

# Ignore warnings of print() usage
# ruff: noqa: T201

# Load credentials from env
base_url = os.getenv("ALATION_BASE_URL")
client_id = os.getenv("ALATION_CLIENT_ID")
client_secret = os.getenv("ALATION_CLIENT_SECRET")
openai_api_key = os.getenv("OPENAI_API_KEY")
auth_method = os.getenv("ALATION_AUTH_METHOD", "service_account")

if not all([base_url, client_id, client_secret, openai_api_key, auth_method]):
    value_error_message = "Missing one or more required environment variables."
    raise ValueError(value_error_message)


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


sdk = initialize_sdk(base_url, auth_method)

# LangChain tools
tools = get_langchain_tools(sdk)

# LLM (OpenAI)
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)

# Create agent using create_agent - returns a directly invokable CompiledStateGraph
agent = create_agent(model=llm, tools=tools, system_prompt="You are a helpful assistant using Alation's metadata catalog.")

# Example 1: Without signature
print("\n=== Example 1: Without Signature ===")
question = "What are the sales tables in our data warehouse?"
response = agent.invoke(
    {
        "messages": [("user", question)],
    }
)
print("\nAgent Response (Without Signature):")
print(response)

# Example 2: With signature
print("\n=== Example 2: With Signature ===")
tables_only_signature = {
    "table": {"fields_required": ["name", "title", "description", "url"]}
}
qa_question = "What tables contain sales data?"
qa_response = agent.invoke(
    {
        "messages": [("user", qa_question)],
        "signature": tables_only_signature,
    }
)
print("\nAgent Response (With Signature):")
print(qa_response)


# Example 3: Bulk retrieval tool
print("\n=== Example 3: Bulk retrieval tool ===")
bulk_table_signature = {
    "table": {
        "fields_required": ["name", "title", "description", "url"],
        "search_filters": {"flags": ["Endorsement"], "fields": {"ds": [1]}},
        "limit": 5,
    }
}
qa_question = f"""Use the bulk_retrieval tool with this exact signature: {json.dumps(bulk_table_signature)}"""

qa_response = agent.invoke({"messages": [("user", qa_question)]})
print("\nAgent Response (Bulk retrieval tool):")
print(qa_response)
