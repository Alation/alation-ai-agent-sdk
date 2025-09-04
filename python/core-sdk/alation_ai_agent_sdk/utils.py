"""
Utility functions for Alation AI Agent SDK.

This module provides common utilities that can be used across different distributions
of the SDK (core, MCP, LangChain, etc.).
"""

from importlib.metadata import version, PackageNotFoundError
from typing import Dict


SDK_VERSION = "UNKNOWN"
try:
    SDK_VERSION = version("alation_ai_agent_sdk")
except PackageNotFoundError:
    pass


def is_tool_enabled(
    tool_name: str,
    disabled_tools: set[str],
    enabled_beta_tools: set[str],
    beta_tools: set[str] | None = None,
) -> bool:
    """
    Check if a tool should be enabled given configuration.

    Args:
        tool_name: Tool identifier (e.g., AlationTools.LINEAGE)
        disabled_tools: Set of disabled tool names
        enabled_beta_tools: Set of enabled beta tool names
        beta_tools: Set of beta tools (defaults to SDK's BETA_TOOLS)

    Returns:
        bool: True if tool should be enabled
    """
    if beta_tools is None:
        # Import here to avoid circular dependency
        from alation_ai_agent_sdk.sdk import AlationAIAgentSDK

        beta_tools = AlationAIAgentSDK.BETA_TOOLS

    if tool_name in disabled_tools:
        return False
    if tool_name not in beta_tools:
        return True
    return tool_name in enabled_beta_tools


def get_tool_metadata(tool_class) -> Dict[str, str]:
    """
    Extract name and description from tool class.

    Args:
        tool_class: Tool class with _get_name() and _get_description() methods

    Returns:
        dict: Dictionary with 'name' and 'description' keys
    """
    return {
        "name": tool_class._get_name(),
        "description": tool_class._get_description(),
    }
