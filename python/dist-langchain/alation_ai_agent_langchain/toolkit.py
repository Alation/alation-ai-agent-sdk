from alation_ai_agent_sdk import AlationAIAgentSDK

from .tool import get_alation_context_tool, get_alation_data_products_tool


def get_tools(sdk: AlationAIAgentSDK):
    return [
        get_alation_context_tool(sdk),
        get_alation_data_products_tool(sdk),
    ]
