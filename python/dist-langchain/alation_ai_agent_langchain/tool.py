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

def get_alation_bulk_retrieval_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    bulk_retrieval_tool = sdk.bulk_retrieval_tool

    def run_with_signature(*args, **kwargs):
        """
        Handles below calling patterns:
        1. bulk_retrieval(signature={"table": {"fields_required": ["name", "url"], "limit": 10}})
        kwargs = {"signature": {"table": {...}}}

        2. bulk_retrieval(args=[{"table": {"fields_required": ["name", "url"], "limit": 10}}])
        kwargs = {"args": ({"table": {...}},)}

        3. bulk_retrieval({"table": {"fields_required": ["name", "url"], "limit": 10}})
        args = ({"table": {...}},)
        """

        signature = None

        # Pattern 1: Called with signature parameter
        if 'signature' in kwargs:
            signature = kwargs['signature']

        # Pattern 2: direct dict without signature keyword
        elif 'args' in kwargs and kwargs['args']:
            signature = kwargs['args'][0]

        # Pattern 3: Positional argument
        elif args and len(args) > 0:
            signature = args[0]

        # Case 4: No signature provided
        else:
            signature = None

        result = bulk_retrieval_tool.run(signature)
        return result

    return StructuredTool.from_function(
        name=bulk_retrieval_tool.name,
        description=bulk_retrieval_tool.description,
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
