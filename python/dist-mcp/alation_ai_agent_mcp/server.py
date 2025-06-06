import os
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams


def create_server():
    # Load Alation credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    auth_method = os.getenv("ALATION_AUTH_METHOD")

    if not base_url or not auth_method:
        raise ValueError(
            "Missing required environment variables: ALATION_BASE_URL and ALATION_AUTH_METHOD"
        )

    if auth_method == "user_account":
        user_id = os.getenv("ALATION_USER_ID")
        refresh_token = os.getenv("ALATION_REFRESH_TOKEN")
        if not user_id or not refresh_token:
            raise ValueError(
                "Missing required environment variables: ALATION_USER_ID and ALATION_REFRESH_TOKEN for 'user_account' auth_method"
            )
        try:
            user_id = int(user_id)
        except ValueError:
            raise ValueError("ALATION_USER_ID must be an integer.")
        auth_params = UserAccountAuthParams(user_id, refresh_token)

    elif auth_method == "service_account":
        client_id = os.getenv("ALATION_CLIENT_ID")
        client_secret = os.getenv("ALATION_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError(
                "Missing required environment variables: ALATION_CLIENT_ID and ALATION_CLIENT_SECRET for 'service_account' auth_method"
            )
        auth_params = ServiceAccountAuthParams(client_id, client_secret)

    else:
        raise ValueError(
            "Invalid ALATION_AUTH_METHOD. Must be 'user_account' or 'service_account'."
        )

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server", version="0.3.0")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(base_url, auth_method, auth_params)

    @mcp.tool(name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description)
    def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
        result = alation_sdk.get_context(question, signature)
        return str(result)

    @mcp.tool(
        name=alation_sdk.data_product_tool.name,
        description=alation_sdk.data_product_tool.description,
    )
    def get_data_products(product_id: Optional[str] = None, query: Optional[str] = None) -> str:
        result = alation_sdk.get_data_products(product_id, query)
        return str(result)

    return mcp


# Delay server instantiation
mcp = None


def run_server():
    """Entry point for running the MCP server"""
    global mcp
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    run_server()
