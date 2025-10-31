from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    AlationTools,
)
from alation_ai_agent_sdk.utils import is_tool_enabled

from .tool import (
    get_alation_context_tool,
    get_alation_bulk_retrieval_tool,
    get_alation_data_products_tool,
    get_analyze_catalog_question_tool,
    get_catalog_context_search_agent_tool,
    get_check_data_quality_tool,
    get_check_job_status_tool,
    get_custom_agent_tool,
    get_custom_fields_definitions_tool,
    get_data_dictionary_instructions_tool,
    get_data_sources_tool,
    get_generate_data_product_tool,
    get_alation_lineage_tool,
    get_query_flow_agent_tool,
    get_signature_creation_tool,
    get_sql_query_agent_tool,
    get_update_catalog_asset_metadata_tool,
)


def get_tools(sdk: AlationAIAgentSDK):
    tools = []
    if is_tool_enabled(
        AlationTools.AGGREGATED_CONTEXT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_alation_context_tool(sdk))
    if is_tool_enabled(
        AlationTools.ANALYZE_CATALOG_QUESTION,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_analyze_catalog_question_tool(sdk))
    if is_tool_enabled(
        AlationTools.BULK_RETRIEVAL,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_alation_bulk_retrieval_tool(sdk))
    if is_tool_enabled(
        AlationTools.CATALOG_CONTEXT_SEARCH_AGENT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_catalog_context_search_agent_tool(sdk))
    if is_tool_enabled(
        AlationTools.CHECK_JOB_STATUS,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_check_job_status_tool(sdk))
    if is_tool_enabled(
        AlationTools.CUSTOM_AGENT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_custom_agent_tool(sdk))
    if is_tool_enabled(
        AlationTools.DATA_QUALITY,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_check_data_quality_tool(sdk))
    if is_tool_enabled(
        AlationTools.GENERATE_DATA_PRODUCT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_generate_data_product_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_custom_fields_definitions_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_data_dictionary_instructions_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_DATA_PRODUCT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_alation_data_products_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_DATA_SOURCES,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_data_sources_tool(sdk))
    if is_tool_enabled(
        AlationTools.LINEAGE,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_alation_lineage_tool(sdk))
    if is_tool_enabled(
        AlationTools.QUERY_FLOW_AGENT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_query_flow_agent_tool(sdk))
    if is_tool_enabled(
        AlationTools.SIGNATURE_CREATION,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_signature_creation_tool(sdk))
    if is_tool_enabled(
        AlationTools.SQL_QUERY_AGENT,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_sql_query_agent_tool(sdk))
    if is_tool_enabled(
        AlationTools.UPDATE_METADATA,
        sdk.enabled_tools,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_update_catalog_asset_metadata_tool(sdk))

    return tools
