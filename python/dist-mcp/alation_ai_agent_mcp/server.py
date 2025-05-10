import os
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK


def create_server():
    # Load Alation credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    user_id_raw = os.getenv("ALATION_USER_ID")
    refresh_token = os.getenv("ALATION_REFRESH_TOKEN")

    if not base_url or not user_id_raw or not refresh_token:
        raise ValueError(
            "Missing required environment variables: ALATION_BASE_URL, ALATION_USER_ID, ALATION_REFRESH_TOKEN"
        )

    user_id = int(user_id_raw)

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server", version="0.1.0")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(base_url, user_id, refresh_token)

    @mcp.tool(name=alation_sdk.context_tool.name)
    def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
        f"""{alation_sdk.context_tool.description}"""
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
