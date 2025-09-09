"""
Core server functionality for Alation MCP Server.

This module provides the main entry point and server creation logic for the Alation MCP Server.
It supports two transport modes:

- STDIO Mode: For direct MCP client connections using stdin/stdout (like Claude Desktop)
- HTTP Mode: For web-based access with OAuth authentication

Architecture:
- STDIO mode creates a shared SDK instance with pre-configured authentication
- HTTP mode uses per-request authentication via FastMCP's dependency injection
- All Alation tools are registered dynamically based on enabled/disabled configuration
"""

from typing import Optional
import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
import uvicorn

from alation_ai_agent_sdk import AlationAIAgentSDK

from .auth import get_stdio_auth_params, AlationTokenVerifier
from .register_tools import (
    register_tools,
)
from .utils import (
    validate_cloud_instance,
    log_initialization_info,
    setup_logging,
    parse_arguments,
    prepare_server_config,
    MCP_SERVER_VERSION,
)


def create_fastmcp_server(
    base_url: str,
    transport_mode: str = "stdio",
    host: str = "localhost",
    port: int = 8000,
    external_url: Optional[str] = None,
) -> FastMCP:
    """
    Create a FastMCP server instance based on transport mode.

    This function handles only the FastMCP server creation with transport-specific
    configuration. Use create_server() for full server setup including tools.

    Args:
        base_url: Alation instance base URL
        transport_mode: Either "stdio" or "http"
        host: Host for HTTP server (only used in HTTP mode)
        port: Port for HTTP server (only used in HTTP mode)
        external_url: External URL for OAuth resource_server_url (use for production hosted MCP server)

    Returns:
        FastMCP server instance configured for the specified transport
    """
    if transport_mode == "stdio":
        # STDIO mode: Simple server without authentication
        return FastMCP(name="Alation MCP Server")

    elif transport_mode == "http":
        # HTTP mode: Server with OAuth authentication
        # Determine the resource server URL (external URL vs internal binding)
        resource_server_url = external_url if external_url else f"http://{host}:{port}"

        auth = AuthSettings(
            issuer_url=AnyHttpUrl(base_url),
            resource_server_url=AnyHttpUrl(resource_server_url),
        )
        return FastMCP(
            name="Alation MCP Server",
            stateless_http=True,
            auth=auth,
            token_verifier=AlationTokenVerifier(base_url),
        )

    else:
        raise ValueError(f"Unknown transport mode: {transport_mode}")


def create_server(
    transport: str,
    base_url: Optional[str] = None,
    disabled_tools_str: Optional[str] = None,
    enabled_beta_tools_str: Optional[str] = None,
    host: str = "localhost",
    port: int = 8000,
    external_url: Optional[str] = None,
) -> FastMCP:
    """
    Create and configure an MCP server for the specified transport mode.

    Args:
        transport: Transport mode ("stdio" or "http")
        base_url: Optional Alation instance base URL (overrides environment variable)
        disabled_tools_str: Optional comma-separated string of disabled tools
        enabled_beta_tools_str: Optional comma-separated string of enabled beta tools
        host: Host for HTTP server (only used in HTTP mode)
        port: Port for HTTP server (only used in HTTP mode)
        external_url: External URL for OAuth resource_server_url (only used in HTTP mode)

    Returns:
        Configured FastMCP server instance
    """
    # Prepare common configuration
    base_url, tools_disabled, beta_tools_enabled = prepare_server_config(
        base_url, disabled_tools_str, enabled_beta_tools_str
    )

    # Create FastMCP server based on transport mode
    mcp = create_fastmcp_server(base_url, transport, host, port, external_url)

    if transport == "stdio":
        # STDIO mode: Create shared SDK instance with environment-based auth
        # This SDK is reused for all tool calls to avoid repeated authentication
        auth_method, auth_params = get_stdio_auth_params()

        alation_sdk = AlationAIAgentSDK(
            base_url,
            auth_method,
            auth_params,
            dist_version=f"mcp-{MCP_SERVER_VERSION}",
        )

        validate_cloud_instance(alation_sdk)
        log_initialization_info(alation_sdk, MCP_SERVER_VERSION)

        # Register tools with explicit tool configuration (same as HTTP mode)
        register_tools(
            mcp,
            alation_sdk=alation_sdk,
            disabled_tools=set(tools_disabled),
            enabled_beta_tools=set(beta_tools_enabled),
        )

    elif transport == "http":
        # HTTP mode: No shared SDK - each tool call creates its own SDK instance
        # Authentication happens per-request via FastMCP's get_access_token()
        # Register tools with explicit tool configuration
        register_tools(
            mcp,
            base_url=base_url,
            disabled_tools=set(tools_disabled),
            enabled_beta_tools=set(beta_tools_enabled),
        )

    else:
        raise ValueError(f"Unknown transport mode: {transport}")

    return mcp


def run_server() -> None:
    """Entry point for running the MCP server."""
    setup_logging()

    (
        transport,
        base_url,
        disabled_tools_str,
        enabled_beta_tools_str,
        host,
        port,
        external_url,
    ) = parse_arguments()

    mcp = create_server(
        transport,
        base_url,
        disabled_tools_str,
        enabled_beta_tools_str,
        host,
        port,
        external_url,
    )

    if transport == "stdio":
        logging.info("Starting Alation MCP STDIO Server")
        mcp.run()
    elif transport == "http":
        logging.info(f"Starting Alation MCP HTTP Server on {host}:{port}")
        logging.info(f"OAuth authentication enabled for {base_url}")
        uvicorn.run(mcp.streamable_http_app, host=host, port=port)
    else:
        raise ValueError(f"Unknown transport mode: {transport}")


if __name__ == "__main__":
    run_server()
