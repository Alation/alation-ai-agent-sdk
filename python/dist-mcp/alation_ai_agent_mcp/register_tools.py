"""Tool registration module for Alation MCP Server."""

from typing import Any, Dict, List, Optional

from alation_ai_agent_sdk import AlationAIAgentSDK, AlationTools
from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadItem
from alation_ai_agent_sdk.lineage import (
    LineageBatchSizeType,
    LineageDesignTimeType,
    LineageDirectionType,
    LineageExcludedSchemaIdsType,
    LineageGraphProcessingType,
    LineageOTypeFilterType,
    LineagePagination,
    LineageRootNode,
    LineageTimestampType,
)
from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """
    Register all available Alation tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        alation_sdk: Initialized Alation SDK instance
    """
    _register_aggregated_context_tool(mcp, alation_sdk)
    _register_bulk_retrieval_tool(mcp, alation_sdk)
    _register_data_product_tool(mcp, alation_sdk)
    _register_update_metadata_tool(mcp, alation_sdk)
    _register_check_job_status_tool(mcp, alation_sdk)
    _register_lineage_tool(mcp, alation_sdk)
    _register_data_quality_tool(mcp, alation_sdk)
    _register_generate_data_product_tool(mcp, alation_sdk)


def _register_aggregated_context_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the aggregated context tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.AGGREGATED_CONTEXT):

        @mcp.tool(
            name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description
        )
        def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
            result = alation_sdk.get_context(question, signature)
            return str(result)


def _register_bulk_retrieval_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the bulk retrieval tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.BULK_RETRIEVAL):

        @mcp.tool(
            name=alation_sdk.bulk_retrieval_tool.name,
            description=alation_sdk.bulk_retrieval_tool.description,
        )
        def alation_bulk_retrieval(signature: Dict[str, Any]) -> str:
            result = alation_sdk.get_bulk_objects(signature)
            return str(result)


def _register_data_product_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the data product tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.DATA_PRODUCT):

        @mcp.tool(
            name=alation_sdk.data_product_tool.name,
            description=alation_sdk.data_product_tool.description,
        )
        def get_data_products(product_id: Optional[str] = None, query: Optional[str] = None) -> str:
            result = alation_sdk.get_data_products(product_id, query)
            return str(result)


def _register_update_metadata_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the update metadata tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.UPDATE_METADATA):

        @mcp.tool(
            name=alation_sdk.update_catalog_asset_metadata_tool.name,
            description=alation_sdk.update_catalog_asset_metadata_tool.description,
        )
        def update_catalog_asset_metadata(
            custom_field_values: list[CatalogAssetMetadataPayloadItem],
        ) -> str:
            result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
            return str(result)


def _register_check_job_status_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the check job status tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.CHECK_JOB_STATUS):

        @mcp.tool(
            name=alation_sdk.check_job_status_tool.name,
            description=alation_sdk.check_job_status_tool.description,
        )
        def check_job_status(job_id: int) -> str:
            result = alation_sdk.check_job_status(job_id)
            return str(result)


def _register_lineage_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the lineage tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.LINEAGE):

        @mcp.tool(
            name=alation_sdk.lineage_tool.name,
            description=alation_sdk.lineage_tool.description,
        )
        def get_lineage(
            root_node: LineageRootNode,
            direction: LineageDirectionType,
            limit: Optional[int] = 1000,
            batch_size: Optional[LineageBatchSizeType] = 1000,
            pagination: Optional[LineagePagination] = None,
            processing_mode: Optional[LineageGraphProcessingType] = None,
            show_temporal_objects: Optional[bool] = False,
            design_time: Optional[LineageDesignTimeType] = None,
            max_depth: Optional[int] = 10,
            excluded_schema_ids: Optional[LineageExcludedSchemaIdsType] = None,
            allowed_otypes: Optional[LineageOTypeFilterType] = None,
            time_from: Optional[LineageTimestampType] = None,
            time_to: Optional[LineageTimestampType] = None,
        ) -> str:
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


def _register_data_quality_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the data quality tool if enabled."""
    if alation_sdk.is_tool_enabled(AlationTools.DATA_QUALITY):

        @mcp.tool(
            name=alation_sdk.check_data_quality_tool.name,
            description=alation_sdk.check_data_quality_tool.description,
        )
        def check_data_quality(
            sql_query: Optional[str] = None,
            output_format: Optional[str] = None,
            table_ids: Optional[list[int]] = None,
            db_uri: Optional[str] = None,
            ds_id: Optional[int] = None,
            bypassed_dq_sources: Optional[list[str]] = None,
            default_schema_name: Optional[str] = None,
            dq_score_threshold: Optional[int] = None,
        ) -> str:
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


def _register_generate_data_product_tool(mcp: FastMCP, alation_sdk: AlationAIAgentSDK) -> None:
    """Register the generate data product tool."""

    @mcp.tool(
        name=alation_sdk.generate_data_product_tool.name,
        description=alation_sdk.generate_data_product_tool.description,
    )
    def generate_data_product() -> str:
        result = alation_sdk.generate_data_product()
        return result
