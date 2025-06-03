from typing import Any

from alation_ai_agent_sdk import AlationAIAgentSDK
from langchain.tools import StructuredTool


def get_alation_context_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    alation_context_tool = sdk.context_tool

    def run_with_signature(question: str, signature: dict[str, Any] | None = None):
        return alation_context_tool.run(question, signature)

    return StructuredTool.from_function(
        name=alation_context_tool.name,
        description=alation_context_tool.description,
        func=run_with_signature,
        args_schema=None,
    )


def get_alation_data_products_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_products_tool = sdk.data_product_tool

    def run_with_query_or_product_id(query_or_product_id: str):
        return data_products_tool.run(query_or_product_id)

    return StructuredTool.from_function(
        name=data_products_tool.name,
        description=data_products_tool.description,
        func=run_with_query_or_product_id,
        args_schema=None,
    )
