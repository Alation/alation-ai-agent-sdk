from alation_ai_agent_sdk import (
    AlationAIAgentSDK,
    AlationTools,
)

from .tool import (
    get_alation_context_tool,
    get_alation_bulk_retrieval_tool,
    get_alation_data_products_tool,
    get_update_catalog_asset_metadata_tool,
    get_check_job_status_tool,
    get_alation_lineage_tool,
)


def get_tools(sdk: AlationAIAgentSDK):
    tools = []
    if sdk.is_tool_enabled(AlationTools.AGGREGATED_CONTEXT):
        tools.append(get_alation_context_tool(sdk))
    if sdk.is_tool_enabled(AlationTools.BULK_RETRIEVAL):
        tools.append(get_alation_bulk_retrieval_tool(sdk))
    if sdk.is_tool_enabled(AlationTools.DATA_PRODUCT):
        tools.append(get_alation_data_products_tool(sdk))
    if sdk.is_tool_enabled(AlationTools.UPDATE_METADATA):
        tools.append(get_update_catalog_asset_metadata_tool(sdk))
    if sdk.is_tool_enabled(AlationTools.CHECK_JOB_STATUS):
        tools.append(get_check_job_status_tool(sdk))
    if sdk.is_tool_enabled(AlationTools.LINEAGE):
        tools.append(get_alation_lineage_tool(sdk))
    return tools
