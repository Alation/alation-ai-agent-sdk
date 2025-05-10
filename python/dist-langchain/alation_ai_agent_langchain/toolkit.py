from alation_ai_agent_sdk import AlationAIAgentSDK

from .tool import get_alation_context_tool


def get_tools(sdk: AlationAIAgentSDK):
    return [get_alation_context_tool(sdk)]
