import argparse
import os
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

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
from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    AlationTools,
    UserAccountAuthParams,
    ServiceAccountAuthParams,
    csv_str_to_tool_list,
)
from alation_ai_agent_sdk.api import CatalogAssetMetadataPayloadItem

import logging

logger = logging.getLogger("alation.mcp.server")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

MCP_SERVER_VERSION = "0.5.0"


def create_server(
    disabled_tools_str: Optional[str] = None, enabled_beta_tools_str: Optional[str] = None
):
    # Load Alation credentials from environment variables
    base_url = os.getenv("ALATION_BASE_URL")
    auth_method = os.getenv("ALATION_AUTH_METHOD")

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

    is_cloud = getattr(alation_sdk.api, "is_cloud", None)
    if is_cloud is None:
        raise RuntimeError(
            "Failed to fetch license info. Unable to determine if the instance is cloud or on-prem."
        )
    if not is_cloud:
        raise RuntimeError("This Alation instance is on-prem. MCP tools require a cloud instance.")

    alation_version = getattr(alation_sdk.api, "alation_release_name", None)
    is_cloud = getattr(alation_sdk.api, "is_cloud", None)
    logger.info(
        f"Alation MCP Server initializing |Alation version: {alation_version} | Cloud instance: {is_cloud} | dist_version: {f'mcp-{MCP_SERVER_VERSION}'}"
    )

    if alation_sdk.is_tool_enabled(AlationTools.AGGREGATED_CONTEXT):

        @mcp.tool(
            name=alation_sdk.context_tool.name, description=alation_sdk.context_tool.description
        )
        def alation_context(question: str, signature: Dict[str, Any] | None = None) -> str:
            result = alation_sdk.get_context(question, signature)
            return str(result)

    if alation_sdk.is_tool_enabled(AlationTools.BULK_RETRIEVAL):

        @mcp.tool(
            name=alation_sdk.bulk_retrieval_tool.name,
            description=alation_sdk.bulk_retrieval_tool.description,
        )
        def alation_bulk_retrieval(signature: Dict[str, Any]) -> str:
            result = alation_sdk.get_bulk_objects(signature)
            return str(result)

    if alation_sdk.is_tool_enabled(AlationTools.DATA_PRODUCT):

        @mcp.tool(
            name=alation_sdk.data_product_tool.name,
            description=alation_sdk.data_product_tool.description,
        )
        def get_data_products(product_id: Optional[str] = None, query: Optional[str] = None) -> str:
            result = alation_sdk.get_data_products(product_id, query)
            return str(result)

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

    if alation_sdk.is_tool_enabled(AlationTools.CHECK_JOB_STATUS):

        @mcp.tool(
            name=alation_sdk.check_job_status_tool.name,
            description=alation_sdk.check_job_status_tool.description,
        )
        def check_job_status(job_id: int) -> str:
            result = alation_sdk.check_job_status(job_id)
            return str(result)

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
          
    @mcp.tool(
        name=alation_sdk.generate_data_product_tool.name,
        description=alation_sdk.generate_data_product_tool.description,
    )
    def generate_data_product() -> str:
        result = alation_sdk.generate_data_product()
        return result

    return mcp


# Delay server instantiation
mcp = None


def run_server():
    parser = argparse.ArgumentParser(description="Alation MCP Server")
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

    """Entry point for running the MCP server"""
    global mcp
    mcp = create_server(
        disabled_tools_str=args.disabled_tools if args else None,
        enabled_beta_tools_str=args.enabled_beta_tools if args else None,
    )
    mcp.run()


if __name__ == "__main__":
    run_server()
