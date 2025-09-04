from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    AlationTools,
)
from alation_ai_agent_sdk.utils import is_tool_enabled

from .tool import (
    get_alation_context_tool,
    get_alation_bulk_retrieval_tool,
    get_alation_data_products_tool,
    get_update_catalog_asset_metadata_tool,
    get_check_job_status_tool,
    get_generate_data_product_tool,
    get_alation_lineage_tool,
    get_check_data_quality_tool,
    get_custom_fields_definitions_tool,
    get_data_dictionary_instructions_tool,
)


def get_tools(sdk: AlationAIAgentSDK):
    tools = []
    if is_tool_enabled(
        AlationTools.AGGREGATED_CONTEXT, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_alation_context_tool(sdk))
    if is_tool_enabled(
        AlationTools.BULK_RETRIEVAL, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_alation_bulk_retrieval_tool(sdk))
    if is_tool_enabled(
        AlationTools.DATA_PRODUCT, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_alation_data_products_tool(sdk))
    if is_tool_enabled(
        AlationTools.UPDATE_METADATA, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_update_catalog_asset_metadata_tool(sdk))
    if is_tool_enabled(
        AlationTools.CHECK_JOB_STATUS, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_check_job_status_tool(sdk))
    if is_tool_enabled(
        AlationTools.LINEAGE, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_alation_lineage_tool(sdk))
    if is_tool_enabled(
        AlationTools.DATA_QUALITY, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_check_data_quality_tool(sdk))
    if is_tool_enabled(
        AlationTools.GENERATE_DATA_PRODUCT, sdk.disabled_tools, sdk.enabled_beta_tools
    ):
        tools.append(get_generate_data_product_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_custom_fields_definitions_tool(sdk))
    if is_tool_enabled(
        AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
        sdk.disabled_tools,
        sdk.enabled_beta_tools,
    ):
        tools.append(get_data_dictionary_instructions_tool(sdk))
    return tools
