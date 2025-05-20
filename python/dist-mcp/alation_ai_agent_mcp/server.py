import os
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK


def create_server():
    # Load Alation credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    user_id_raw = os.getenv("ALATION_USER_ID")
    refresh_token = os.getenv("ALATION_REFRESH_TOKEN")
    client_id = os.getenv("ALATION_CLIENT_ID")
    client_secret = os.getenv("ALATION_CLIENT_SECRET")

    if not base_url or not ((user_id_raw and refresh_token) or (client_id and client_secret)):
        raise ValueError(
            "Missing required environment variables: ALATION_BASE_URL and either "
            "(ALATION_USER_ID + ALATION_REFRESH_TOKEN) or (ALATION_CLIENT_ID + ALATION_CLIENT_SECRET)"
        )

    user_id = int(user_id_raw)

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server", version="0.1.0")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(base_url, user_id, refresh_token, client_id, client_secret)

    @mcp.tool(name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description)
    def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
        result = alation_sdk.get_context(question, signature)
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
