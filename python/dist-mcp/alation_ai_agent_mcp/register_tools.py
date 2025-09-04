"""
Tool registration module for Alation MCP Server.

This module handles the registration and management of Alation tools with the FastMCP server.
It provides a clean abstraction between the Alation SDK tools and the MCP protocol.

Key Components:
- create_sdk_for_tool(): Factory function for SDK instances
- register_tools(): Main registration function
- is_tool_enabled(): Helper to check if a tool is enabled

Authentication Patterns:
- STDIO mode: Uses a shared, pre-configured AlationAIAgentSDK instance
- HTTP mode: Creates per-request SDK instances using FastMCP's get_access_token()

Each tool is conditionally registered based on SDK configuration. Tools use the
get_tool_metadata() utility function for consistent metadata retrieval.
"""

from typing import Any, Dict
import logging

from alation_ai_agent_sdk import AlationAIAgentSDK, AlationTools, BearerTokenAuthParams
from alation_ai_agent_sdk.utils import is_tool_enabled, get_tool_metadata
from alation_ai_agent_sdk.tools import (
    AlationContextTool,
    AlationBulkRetrievalTool,
    AlationGetDataProductTool,
    UpdateCatalogAssetMetadataTool,
    CheckJobStatusTool,
    AlationLineageTool,
    CheckDataQualityTool,
    GenerateDataProductTool,
    GetCustomFieldsDefinitionsTool,
    GetDataDictionaryInstructionsTool,
)
from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

from .utils import MCP_SERVER_VERSION

logger = logging.getLogger(__name__)


def register_tools(
    mcp: FastMCP,
    alation_sdk: AlationAIAgentSDK | None = None,
    base_url: str | None = None,
    disabled_tools: set[str] | None = None,
    enabled_beta_tools: set[str] | None = None,
) -> None:
    """
    Register Alation tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        alation_sdk: Pre-configured SDK instance for STDIO mode (optional)
        base_url: Base URL for HTTP mode (required for HTTP mode)
        disabled_tools: Set of disabled tools (required)
        enabled_beta_tools: Set of enabled beta tools (required)
    """

    # Pre-calculate tool configuration for use in tool registrations
    config_disabled = disabled_tools or set()
    config_enabled_beta = enabled_beta_tools or set()

    def create_sdk_for_tool() -> AlationAIAgentSDK:
        """Create SDK instance for tool execution with appropriate authentication."""
        if alation_sdk:
            # STDIO mode: use the shared SDK instance
            return alation_sdk
        else:
            # HTTP mode: create per-request SDK instance
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
                base_url=base_url,
                auth_method="bearer_token",
                auth_params=auth_params,
                dist_version=f"mcp-{MCP_SERVER_VERSION}",
            )
        except ValueError as e:
            logger.error(f"Authentication error in HTTP mode: {e}")
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.error(f"Failed to create HTTP SDK: {e}")
            raise RuntimeError(f"SDK initialization failed: {e}") from e

    if is_tool_enabled(
        AlationTools.AGGREGATED_CONTEXT, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(AlationContextTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def alation_context(question: str, signature: Dict[str, Any] | None = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_context(question, signature)
            return result

    if is_tool_enabled(
        AlationTools.BULK_RETRIEVAL, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(AlationBulkRetrievalTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def alation_bulk_retrieval(signature: dict):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_bulk_objects(signature)
            return result

    if is_tool_enabled(AlationTools.DATA_PRODUCT, config_disabled, config_enabled_beta):
        metadata = get_tool_metadata(AlationGetDataProductTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_products(product_id: str | None = None, query: str | None = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_products(product_id, query)
            return result

    if is_tool_enabled(
        AlationTools.UPDATE_METADATA, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(UpdateCatalogAssetMetadataTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def update_catalog_asset_metadata(custom_field_values: list):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
            return result

    if is_tool_enabled(
        AlationTools.CHECK_JOB_STATUS, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(CheckJobStatusTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def check_job_status(job_id: int):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.check_job_status(job_id)
            return result

    if is_tool_enabled(AlationTools.LINEAGE, config_disabled, config_enabled_beta):
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

        metadata = get_tool_metadata(AlationLineageTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
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
        ):
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
            return result

    if is_tool_enabled(AlationTools.DATA_QUALITY, config_disabled, config_enabled_beta):
        metadata = get_tool_metadata(CheckDataQualityTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def check_data_quality(
            table_ids: list | None = None,
            sql_query: str | None = None,
            db_uri: str | None = None,
            ds_id: int | None = None,
            bypassed_dq_sources: list | None = None,
            default_schema_name: str | None = None,
            output_format: str | None = None,
            dq_score_threshold: int | None = None,
        ) -> dict | str:
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
            return result

    if is_tool_enabled(
        AlationTools.GENERATE_DATA_PRODUCT, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(GenerateDataProductTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def generate_data_product() -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.generate_data_product()
            return result

    if is_tool_enabled(
        AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(GetCustomFieldsDefinitionsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_custom_fields_definitions():
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_custom_fields_definitions()
            return result

    if is_tool_enabled(
        AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetDataDictionaryInstructionsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_dictionary_instructions():
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_dictionary_instructions()
            return result
