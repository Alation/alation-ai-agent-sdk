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

from typing import Any, Dict, Optional
import logging

from alation_ai_agent_sdk import (
    AgentSDKOptions,
    AlationAIAgentSDK,
    AlationTools,
    BearerTokenAuthParams,
)
from alation_ai_agent_sdk.types import Filter
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
    SignatureCreationTool,
    AnalyzeCatalogQuestionTool,
    BiReportSearchTool,
    BiReportAgentTool,
    CatalogContextSearchAgentTool,
    CatalogSearchAgentTool,
    ChartCreateAgentTool,
    DataProductQueryAgentTool,
    DeepResearchAgentTool,
    QueryFlowAgentTool,
    SqlQueryAgentTool,
    SqlExecutionTool,
    GenerateChartFromSqlAndCodeTool,
    GetDataSchemaTool,
    GetDataSourcesTool,
    ListDataProductsTool,
    SearchCatalogTool,
    GetSearchFilterFieldsTool,
    GetSearchFilterValuesTool,
    CustomAgentTool,
)
from mcp.server.fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

from .utils import MCP_SERVER_VERSION

logger = logging.getLogger(__name__)


def register_tools(
    mcp: FastMCP,
    alation_sdk: AlationAIAgentSDK | None = None,
    base_url: Optional[str] = None,
    enabled_tools: set[str] | None = None,
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
    config_enabled = enabled_tools or set()
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
                sdk_options=AgentSDKOptions(enable_streaming=True),
            )
        except ValueError as e:
            logger.error(f"Authentication error in HTTP mode: {e}")
            raise  # Re-raise ValueError as-is
        except Exception as e:
            logger.error(f"Failed to create HTTP SDK: {e}")
            raise RuntimeError(f"SDK initialization failed: {e}") from e

    """
      Previously we could get away with simply exporting everything that wasn't disabled.
      That is no longer the case as we're clocking in at 28 tools (including agents as tools).
    """
    if len(config_enabled) == 0:
        # TODO: evaluate this set of tools and agents together
        config_enabled = set(
            [
                # Tools
                AlationTools.AGGREGATED_CONTEXT,
                AlationTools.ANALYZE_CATALOG_QUESTION,
                AlationTools.BULK_RETRIEVAL,
                AlationTools.GENERATE_DATA_PRODUCT,
                AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS,
                AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
                AlationTools.GET_DATA_PRODUCT,
                AlationTools.SIGNATURE_CREATION,
                # Agents as Tools
                AlationTools.CUSTOM_AGENT,
                AlationTools.CATALOG_CONTEXT_SEARCH_AGENT,
                AlationTools.QUERY_FLOW_AGENT,
                AlationTools.CHART_CREATE_AGENT,
                AlationTools.SQL_QUERY_AGENT,
            ]
        )

    if is_tool_enabled(
        AlationTools.AGGREGATED_CONTEXT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(AlationContextTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def alation_context(
            question: str,
            signature: Optional[Dict[str, Any]] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_context(question, signature, chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.BULK_RETRIEVAL,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(AlationBulkRetrievalTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def alation_bulk_retrieval(
            signature: Optional[dict] = None, chat_id: Optional[str] = None
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_bulk_objects(signature, chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.GET_DATA_PRODUCT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(AlationGetDataProductTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_products(
            product_id: Optional[str] = None, query: Optional[str] = None
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_products(product_id, query)
            return result

    if is_tool_enabled(
        AlationTools.UPDATE_METADATA,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(UpdateCatalogAssetMetadataTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def update_catalog_asset_metadata(custom_field_values: list):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.update_catalog_asset_metadata(custom_field_values)
            return result

    if is_tool_enabled(
        AlationTools.CHECK_JOB_STATUS,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(CheckJobStatusTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def check_job_status(job_id: int):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.check_job_status(job_id)
            return result

    if is_tool_enabled(
        AlationTools.LINEAGE, config_enabled, config_disabled, config_enabled_beta
    ):
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

    if is_tool_enabled(
        AlationTools.DATA_QUALITY, config_enabled, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(CheckDataQualityTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def check_data_quality(
            table_ids: list | None = None,
            sql_query: Optional[str] = None,
            db_uri: Optional[str] = None,
            ds_id: int | None = None,
            bypassed_dq_sources: list | None = None,
            default_schema_name: Optional[str] = None,
            output_format: Optional[str] = None,
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
        AlationTools.GENERATE_DATA_PRODUCT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GenerateDataProductTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def generate_data_product() -> str:
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.generate_data_product()
            return result

    if is_tool_enabled(
        AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetCustomFieldsDefinitionsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_custom_fields_definitions(chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_custom_fields_definitions(chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetDataDictionaryInstructionsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_dictionary_instructions():
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_dictionary_instructions()
            return result

    if is_tool_enabled(
        AlationTools.SIGNATURE_CREATION,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(SignatureCreationTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_signature_creation_instructions(chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_signature_creation_instructions(chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.ANALYZE_CATALOG_QUESTION,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(AnalyzeCatalogQuestionTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def analyze_catalog_question(question: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.analyze_catalog_question(question, chat_id=chat_id)
            return result

    # BI Report Tools
    if is_tool_enabled(
        AlationTools.BI_REPORT_SEARCH,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(BiReportSearchTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def bi_report_search(
            search_term: str, limit: int = 20, filters: list[Filter] | None = None, chat_id: Optional[str] = None
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.search_bi_reports(
                search_term=search_term, limit=limit, filters=filters, chat_id=chat_id
            )
            return result

    if is_tool_enabled(
        AlationTools.BI_REPORT_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(BiReportAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def bi_report_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.bi_report_agent(message=message, chat_id=chat_id)
            return result

    # Catalog Search Tools
    if is_tool_enabled(
        AlationTools.CATALOG_CONTEXT_SEARCH_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(CatalogContextSearchAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def catalog_context_search_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.catalog_context_search_agent(
                message=message, chat_id=chat_id
            )
            return result

    if is_tool_enabled(
        AlationTools.CATALOG_SEARCH_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(CatalogSearchAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def catalog_search_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.catalog_search_agent(message=message, chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.CATALOG_SEARCH,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(SearchCatalogTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def search_catalog_tool(
            search_term: str,
            object_types: list | None = None,
            filters: list[Filter] | None = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.search_catalog_tool(
                search_term=search_term,
                object_types=object_types,
                filters=filters,
                chat_id=chat_id,
            )
            return result

    # Chart and Visualization Tools
    if is_tool_enabled(
        AlationTools.CHART_CREATE_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(ChartCreateAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def chart_create_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.chart_create_agent(message=message, chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.GENERATE_CHART_FROM_SQL_AND_CODE,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GenerateChartFromSqlAndCodeTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def generate_chart_from_sql_and_code_tool(
            data_product_id: str,
            sql: str,
            chart_code_snippet: str,
            image_title: str,
            pre_exec_sql: Optional[str] = None,
            auth_id: Optional[str] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.generate_chart_from_sql_and_code_tool(
                data_product_id=data_product_id,
                sql=sql,
                chart_code_snippet=chart_code_snippet,
                image_title=image_title,
                pre_exec_sql=pre_exec_sql,
                auth_id=auth_id,
                chat_id=chat_id,
            )
            return result

    # Data Product Tools
    if is_tool_enabled(
        AlationTools.DATA_PRODUCT_QUERY_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(DataProductQueryAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def data_product_query_agent(
            message: str,
            data_product_id: str,
            auth_id: Optional[str] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.data_product_query_agent(
                message=message,
                data_product_id=data_product_id,
                auth_id=auth_id,
                chat_id=chat_id,
            )
            return result

    if is_tool_enabled(
        AlationTools.LIST_DATA_PRODUCTS,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(ListDataProductsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def list_data_products_tool(
            search_term: str,
            limit: int = 5,
            marketplace_id: Optional[str] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.list_data_products_tool(
                search_term=search_term,
                limit=limit,
                marketplace_id=marketplace_id,
                chat_id=chat_id,
            )
            return result

    if is_tool_enabled(
        AlationTools.GET_DATA_SCHEMA,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetDataSchemaTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_schema_tool(
            data_product_id: str,
            pre_exec_sql: Optional[str] = None,
            auth_id: Optional[str] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_schema_tool(
                data_product_id=data_product_id,
                pre_exec_sql=pre_exec_sql,
                auth_id=auth_id,
                chat_id=chat_id,
            )
            return result

    if is_tool_enabled(
        AlationTools.GET_DATA_SOURCES,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetDataSourcesTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_data_sources_tool(limit: int = 100, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_data_sources_tool(limit=limit, chat_id=chat_id)
            return result

    # SQL and Query Tools
    if is_tool_enabled(
        AlationTools.SQL_QUERY_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(SqlQueryAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def sql_query_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.sql_query_agent(message=message, chat_id=chat_id)
            return result

    if is_tool_enabled(
        AlationTools.SQL_EXECUTION, config_enabled, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(SqlExecutionTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def sql_execution_tool(
            data_product_id: str,
            sql: str,
            result_table_name: str,
            pre_exec_sql: Optional[str] = None,
            auth_id: Optional[str] = None,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.sql_execution_tool(
                data_product_id=data_product_id,
                sql=sql,
                result_table_name=result_table_name,
                pre_exec_sql=pre_exec_sql,
                auth_id=auth_id,
                chat_id=chat_id,
            )
            return result

    if is_tool_enabled(
        AlationTools.QUERY_FLOW_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(QueryFlowAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def query_flow_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.query_flow_agent(message=message, chat_id=chat_id)
            return result

    # Research and Analysis Tools
    if is_tool_enabled(
        AlationTools.DEEP_RESEARCH_AGENT,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(DeepResearchAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def deep_research_agent(message: str, chat_id: Optional[str] = None):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.deep_research_agent(message=message, chat_id=chat_id)
            return result

    # Search Filter Tools
    if is_tool_enabled(
        AlationTools.GET_SEARCH_FILTER_FIELDS,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetSearchFilterFieldsTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_search_filter_fields_tool(
            search_term: str, limit: int = 10, chat_id: Optional[str] = None
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_search_filter_fields_tool(
                search_term=search_term, limit=limit, chat_id=chat_id
            )
            return result

    if is_tool_enabled(
        AlationTools.GET_SEARCH_FILTER_VALUES,
        config_enabled,
        config_disabled,
        config_enabled_beta,
    ):
        metadata = get_tool_metadata(GetSearchFilterValuesTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def get_search_filter_values_tool(
            field_id: int,
            search_term: str,
            limit: int = 10,
            chat_id: Optional[str] = None,
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.get_search_filter_values_tool(
                field_id=field_id, search_term=search_term, limit=limit, chat_id=chat_id
            )
            return result

    # Custom Agent Tool
    if is_tool_enabled(
        AlationTools.CUSTOM_AGENT, config_enabled, config_disabled, config_enabled_beta
    ):
        metadata = get_tool_metadata(CustomAgentTool)

        @mcp.tool(name=metadata["name"], description=metadata["description"])
        def custom_agent(
            agent_config_id: str, payload: dict, chat_id: Optional[str] = None
        ):
            alation_sdk = create_sdk_for_tool()
            result = alation_sdk.custom_agent(
                agent_config_id=agent_config_id, payload=payload, chat_id=chat_id
            )
            return result
