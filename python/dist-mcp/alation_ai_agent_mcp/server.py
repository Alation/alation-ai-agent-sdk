"""Core server functionality for Alation MCP Server."""

from typing import Optional

from mcp.server.fastmcp import FastMCP
from alation_ai_agent_sdk import AlationAIAgentSDK

from .auth import get_auth_params
from .register_tools import register_tools
from .utils import (
    validate_cloud_instance,
    log_initialization_info,
    setup_logging,
    parse_arguments,
    get_base_url,
    get_tool_configuration,
)

MCP_SERVER_VERSION = "0.5.0"


def create_server(
    base_url: Optional[str] = None,
    disabled_tools_str: Optional[str] = None,
    enabled_beta_tools_str: Optional[str] = None,
) -> FastMCP:
    """
    Create and configure the MCP server with Alation tools.

    Args:
        base_url: Optional Alation instance base URL (overrides environment variable)
        disabled_tools_str: Optional comma-separated string of disabled tools
        enabled_beta_tools_str: Optional comma-separated string of enabled beta tools

    Returns:
        Configured FastMCP server instance
    """
    # Load server configuration
    base_url = get_base_url(base_url)

    # Load authentication parameters
    auth_method, auth_params = get_auth_params()

    # Get tool configuration
    tools_disabled, beta_tools_enabled = get_tool_configuration(
        disabled_tools_str, enabled_beta_tools_str
    )

    # Initialize FastMCP server
    mcp = FastMCP(name="Alation MCP Server")

    # Initialize Alation SDK
    alation_sdk = AlationAIAgentSDK(
        base_url,
        auth_method,
        auth_params,
        dist_version=f"mcp-{MCP_SERVER_VERSION}",
        disabled_tools=set(tools_disabled),
        enabled_beta_tools=set(beta_tools_enabled),
    )

    # Validate cloud instance
    validate_cloud_instance(alation_sdk)

    # Log initialization info
    log_initialization_info(alation_sdk, MCP_SERVER_VERSION)

    # Register all tools
    register_tools(mcp, alation_sdk)

    return mcp


def run_server() -> None:
    """Entry point for running the MCP server."""
    setup_logging()

    base_url, disabled_tools_str, enabled_beta_tools_str = parse_arguments()

    mcp = create_server(
        base_url=base_url,
        disabled_tools_str=disabled_tools_str,
        enabled_beta_tools_str=enabled_beta_tools_str,
    )

    mcp.run()


if __name__ == "__main__":
    run_server()
