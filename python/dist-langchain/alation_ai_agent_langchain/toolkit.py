from alation_ai_agent_sdk import AlationAIAgentSDK

from .tool import (
    get_alation_context_tool,
    get_alation_bulk_retrieval_tool,
    get_alation_data_products_tool,
    get_update_catalog_asset_metadata_tool,
    get_check_job_status_tool,
)


def get_tools(sdk: AlationAIAgentSDK):
    return [
        get_update_catalog_asset_metadata_tool(sdk),
        get_alation_context_tool(sdk),
        get_alation_bulk_retrieval_tool(sdk),
        get_alation_data_products_tool(sdk),
        get_check_job_status_tool(sdk),
    ]
