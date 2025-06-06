from typing import Any, Optional

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

    def run_with_args(product_id: Optional[str] = None, query: Optional[str] = None):
        return data_products_tool.run(product_id=product_id, query=query)

    return StructuredTool.from_function(
        name=data_products_tool.name,
        description=data_products_tool.description,
        func=run_with_args,
        args_schema=None,
    )
