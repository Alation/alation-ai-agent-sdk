"""
Tool registry module for Alation MCP Server.

This module handles the registration and management of Alation tools with the FastMCP server.
It provides a clean abstraction between the Alation SDK tools and the MCP protocol.

Key Components:
- TOOL_REGISTRY: Static metadata for all available tools
- register_tools(): Main function that registers tools with the MCP server
- Tool configuration management (enabled/disabled/beta tools)

Authentication Patterns:
- STDIO mode: Uses a shared, pre-configured AlationAIAgentSDK instance
- HTTP mode: Creates per-request SDK instances using FastMCP's get_access_token()

Each tool is conditionally registered based on the enabled_tools_dict configuration.
"""

from typing import Dict
from dataclasses import dataclass
import logging

from alation_ai_agent_sdk import AlationAIAgentSDK, AlationTools, BearerTokenAuthParams
from alation_ai_agent_sdk.tools import (
    AlationContextTool,
    AlationBulkRetrievalTool,
    AlationGetDataProductTool,
    UpdateCatalogAssetMetadataTool,
    CheckJobStatusTool,
    AlationLineageTool,
    CheckDataQualityTool,
    GenerateDataProductTool,
)
from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

logger = logging.getLogger(__name__)


@dataclass
class ToolMetadata:
    """Metadata for a tool that can be obtained without initializing the SDK."""

    name: str
    description: str
    tool_enum: str


# Registry of all available tools with their static metadata
TOOL_REGISTRY = {
    AlationTools.AGGREGATED_CONTEXT: ToolMetadata(
        name=AlationContextTool._get_name(),
        description=AlationContextTool._get_description(),
        tool_enum=AlationTools.AGGREGATED_CONTEXT,
    ),
    AlationTools.BULK_RETRIEVAL: ToolMetadata(
        name=AlationBulkRetrievalTool._get_name(),
        description=AlationBulkRetrievalTool._get_description(),
        tool_enum=AlationTools.BULK_RETRIEVAL,
    ),
    AlationTools.DATA_PRODUCT: ToolMetadata(
        name=AlationGetDataProductTool._get_name(),
        description=AlationGetDataProductTool._get_description(),
        tool_enum=AlationTools.DATA_PRODUCT,
    ),
    AlationTools.UPDATE_METADATA: ToolMetadata(
        name=UpdateCatalogAssetMetadataTool._get_name(),
        description=UpdateCatalogAssetMetadataTool._get_description(),
        tool_enum=AlationTools.UPDATE_METADATA,
    ),
    AlationTools.CHECK_JOB_STATUS: ToolMetadata(
        name=CheckJobStatusTool._get_name(),
        description=CheckJobStatusTool._get_description(),
        tool_enum=AlationTools.CHECK_JOB_STATUS,
    ),
    AlationTools.LINEAGE: ToolMetadata(
        name=AlationLineageTool._get_name(),
        description=AlationLineageTool._get_description(),
        tool_enum=AlationTools.LINEAGE,
    ),
    AlationTools.DATA_QUALITY: ToolMetadata(
        name=CheckDataQualityTool._get_name(),
        description=CheckDataQualityTool._get_description(),
        tool_enum=AlationTools.DATA_QUALITY,
    ),
    AlationTools.GENERATE_DATA_PRODUCT: ToolMetadata(
        name=GenerateDataProductTool._get_name(),
        description=GenerateDataProductTool._get_description(),
        tool_enum=AlationTools.GENERATE_DATA_PRODUCT,
    ),
}


def get_enabled_tools(
    disabled_tools: set[str], enabled_beta_tools: set[str]
) -> Dict[str, ToolMetadata]:
    """
    Get the list of enabled tools based on configuration.

    Args:
        disabled_tools: Set of disabled tool names
        enabled_beta_tools: Set of enabled beta tool names

    Returns:
        Dictionary mapping tool enum to ToolMetadata for enabled tools
    """
    enabled_tools = {}

    for tool_enum, metadata in TOOL_REGISTRY.items():
        # Check if tool is disabled
        if tool_enum in disabled_tools:
            continue

        # Check if it's a beta tool that needs explicit enabling
        beta_tools = {AlationTools.DATA_QUALITY, AlationTools.GENERATE_DATA_PRODUCT}
        if tool_enum in beta_tools and tool_enum not in enabled_beta_tools:
            continue

        enabled_tools[tool_enum] = metadata

    return enabled_tools


def register_tools(
    mcp: FastMCP,
    alation_sdk: AlationAIAgentSDK | None = None,
    enabled_tools_dict: Dict[str, ToolMetadata] | None = None,
    base_url: str | None = None,
) -> None:
    """
    Register Alation tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        alation_sdk: Pre-configured SDK instance for STDIO mode (optional)
        enabled_tools_dict: Dictionary of enabled tools (auto-detected if not provided)
        base_url: Base URL for HTTP mode (required for HTTP mode)
    """

    # Auto-detect enabled tools if not provided
    if enabled_tools_dict is None:
        if alation_sdk:
            enabled_tools_dict = get_enabled_tools_from_sdk(alation_sdk)
        else:
            # For HTTP mode, include all tools since we don't have an SDK yet
            enabled_tools_dict = {
                tool_enum: metadata for tool_enum, metadata in TOOL_REGISTRY.items()
            }

    def create_sdk_for_tool() -> AlationAIAgentSDK:
        """Create SDK instance for tool execution with supported authentication."""
        if alation_sdk:
            # STDIO mode: if the sdk is present, it means we are using the shared model
            return alation_sdk
        else:
            # HTTP mode: if not, we create one for each tool
            return _create_http_sdk()

    def _create_http_sdk() -> AlationAIAgentSDK:
        """Create SDK for HTTP mode using request authentication."""
        if not base_url:
            raise ValueError("Base URL required for HTTP mode")

        try:
            access_token = get_access_token()
            if access_token is None:
                raise ValueError("No authenticated user found. Authorization required.")

            auth_params = BearerTokenAuthParams(token=access_token.token)
            return AlationAIAgentSDK(
                base_url=base_url, auth_method="bearer_token", auth_params=auth_params
            )
        except Exception as e:
            logger.error(f"Failed to create HTTP SDK: {e}")
            raise RuntimeError(f"Authentication required: {e}") from e

    if AlationTools.AGGREGATED_CONTEXT in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.AGGREGATED_CONTEXT]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def alation_context(question: str, signature: dict = None) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_context(question)
            return str(result)

    if AlationTools.BULK_RETRIEVAL in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.BULK_RETRIEVAL]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def alation_bulk_retrieval(signature: dict) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_bulk_objects(signature)
            return str(result)

    if AlationTools.DATA_PRODUCT in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.DATA_PRODUCT]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def get_data_products(product_id: str | None = None, query: str | None = None) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_products(product_id, query)
            return str(result)

    if AlationTools.UPDATE_METADATA in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.UPDATE_METADATA]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def update_catalog_asset_metadata(custom_field_values: list) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
            return str(result)

    if AlationTools.CHECK_JOB_STATUS in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.CHECK_JOB_STATUS]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def check_job_status(job_id: int) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.check_job_status(job_id)
            return str(result)

    if AlationTools.LINEAGE in enabled_tools_dict:
        from alation_ai_agent_sdk.lineage import (
            LineageRootNode,
            LineageDirectionType,
            LineageBatchSizeType,
            LineagePagination,
            LineageGraphProcessingType,
            LineageDesignTimeType,
            LineageExcludedSchemaIdsType,
            LineageOTypeFilterType,
            LineageTimestampType,
        )

        metadata = enabled_tools_dict[AlationTools.LINEAGE]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def get_lineage(
            root_node: LineageRootNode,
            direction: LineageDirectionType,
            limit: int | None = 1000,
            batch_size: LineageBatchSizeType | None = 1000,
            pagination: LineagePagination | None = None,
            processing_mode: LineageGraphProcessingType | None = None,
            show_temporal_objects: bool | None = False,
            design_time: LineageDesignTimeType | None = None,
            max_depth: int | None = 10,
            excluded_schema_ids: LineageExcludedSchemaIdsType | None = None,
            allowed_otypes: LineageOTypeFilterType | None = None,
            time_from: LineageTimestampType | None = None,
            time_to: LineageTimestampType | None = None,
        ) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_lineage(
                root_node=root_node,
                direction=direction,
                limit=limit,
                batch_size=batch_size,
                pagination=pagination,
                processing_mode=processing_mode,
                show_temporal_objects=show_temporal_objects,
                design_time=design_time,
                max_depth=max_depth,
                excluded_schema_ids=excluded_schema_ids,
                allowed_otypes=allowed_otypes,
                time_from=time_from,
                time_to=time_to,
            )
            return str(result)

    if AlationTools.DATA_QUALITY in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.DATA_QUALITY]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def check_data_quality(
            table_ids: list | None = None,
            sql_query: str | None = None,
            db_uri: str | None = None,
            ds_id: int | None = None,
            bypassed_dq_sources: list | None = None,
            default_schema_name: str | None = None,
            output_format: str | None = None,
            dq_score_threshold: int | None = None,
        ) -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.check_data_quality(
                table_ids=table_ids,
                sql_query=sql_query,
                db_uri=db_uri,
                ds_id=ds_id,
                bypassed_dq_sources=bypassed_dq_sources,
                default_schema_name=default_schema_name,
                output_format=output_format,
                dq_score_threshold=dq_score_threshold,
            )
            return str(result)

    if AlationTools.GENERATE_DATA_PRODUCT in enabled_tools_dict:
        metadata = enabled_tools_dict[AlationTools.GENERATE_DATA_PRODUCT]

        @mcp.tool(name=metadata.name, description=metadata.description)
        def generate_data_product() -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.generate_data_product()
            return str(result)


def get_enabled_tools_from_sdk(alation_sdk: AlationAIAgentSDK) -> Dict[str, ToolMetadata]:
    """Get enabled tools by checking the SDK's configuration."""
    enabled_tools_dict = {}
    for tool_enum, metadata in TOOL_REGISTRY.items():
        if alation_sdk.is_tool_enabled(tool_enum):
            enabled_tools_dict[tool_enum] = metadata
    return enabled_tools_dict
