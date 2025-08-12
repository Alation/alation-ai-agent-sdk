"""Utility functions for Alation MCP Server."""

import os
import argparse
import logging
from typing import Optional, Tuple
from alation_ai_agent_sdk import AlationAIAgentSDK

from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    csv_str_to_tool_list,
)

logger = logging.getLogger("alation.mcp.server")


def setup_logging() -> None:
    """Set up logging configuration for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_base_url(base_url_override: Optional[str] = None) -> str:
    """
    Get the Alation base URL from CLI argument or environment variable.

    Args:
        base_url_override: Optional base URL override from command line

    Returns:
        str: The Alation base URL

    Raises:
        ValueError: If no base URL is provided
    """
    base_url = base_url_override or os.getenv("ALATION_BASE_URL")
    if not base_url:
        raise ValueError(
            "Missing Alation base URL. Provide via --base-url argument or ALATION_BASE_URL environment variable"
        )
    return base_url


def parse_arguments() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse command-line arguments for the MCP server.

    Returns:
        Tuple of (base_url, disabled_tools_str, enabled_beta_tools_str)
    """
    parser = argparse.ArgumentParser(description="Alation MCP Server")
    parser.add_argument(
        "--base-url",
        type=str,
        help="Alation instance base URL (can also be set via ALATION_BASE_URL env var)",
        required=False,
    )
    parser.add_argument(
        "--disabled-tools",
        type=str,
        help="Comma-separated list of tools to disable",
        required=False,
    )
    parser.add_argument(
        "--enabled-beta-tools",
        type=str,
        help="Comma-separated list of beta tools to enable",
        required=False,
    )
    # Uses parse_known_args() to prevent exit(2) when there are unknown arguments
    args = parser.parse_known_args()[0]

    return args.base_url, args.disabled_tools, args.enabled_beta_tools


def validate_cloud_instance(alation_sdk: AlationAIAgentSDK) -> None:
    """
    Validate that the Alation instance is a cloud instance.

    Args:
        alation_sdk: Initialized Alation SDK instance

    Raises:
        RuntimeError: If instance is confirmed to be on-prem
    """
    is_cloud = getattr(alation_sdk.api, "is_cloud", None)
    if is_cloud is not None and not is_cloud:
        raise RuntimeError("This Alation instance is on-prem. MCP tools require a cloud instance.")


def log_initialization_info(alation_sdk: AlationAIAgentSDK, mcp_server_version: str) -> None:
    """
    Log initialization information for the MCP server.

    Args:
        alation_sdk: Initialized Alation SDK instance
        mcp_server_version: Version of the MCP server
    """
    alation_version = getattr(alation_sdk.api, "alation_release_name", None)
    logger.info(
        f"Alation MCP Server initializing | Alation version: {alation_version} | "
        f"dist_version: mcp-{mcp_server_version}"
    )


def get_tool_configuration(
    disabled_tools_str: Optional[str] = None, enabled_beta_tools_str: Optional[str] = None
) -> tuple[list, list]:
    """
    Get tool configuration from environment variables or provided parameters.

    Args:
        disabled_tools_str: Optional comma-separated string of disabled tools
        enabled_beta_tools_str: Optional comma-separated string of enabled beta tools

    Returns:
        tuple: (tools_disabled, beta_tools_enabled)
    """
    tools_disabled = csv_str_to_tool_list(
        disabled_tools_str
        if disabled_tools_str is not None
        else os.getenv("ALATION_DISABLED_TOOLS")
    )
    beta_tools_enabled = csv_str_to_tool_list(
        enabled_beta_tools_str
        if enabled_beta_tools_str is not None
        else os.getenv("ALATION_ENABLED_BETA_TOOLS")
    )

    return tools_disabled, beta_tools_enabled
