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


def get_check_data_quality_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    check_data_quality_tool = sdk.check_data_quality_tool

    def run_with_args(
        table_ids: Optional[list] = None,
        sql_query: Optional[str] = None,
        db_uri: Optional[str] = None,
        ds_id: Optional[int] = None,
        bypassed_dq_sources: Optional[list] = None,
        default_schema_name: Optional[str] = "public",
        output_format: Optional[str] = "JSON",
        dq_score_threshold: Optional[int] = None,
    ):
        return check_data_quality_tool.run(
            table_ids=table_ids,
            sql_query=sql_query,
            db_uri=db_uri,
            ds_id=ds_id,
            bypassed_dq_sources=bypassed_dq_sources,
            default_schema_name=default_schema_name,
            output_format=output_format,
            dq_score_threshold=dq_score_threshold,
        )

    return StructuredTool.from_function(
        name=check_data_quality_tool.name,
        description=check_data_quality_tool.description,
        func=run_with_args,
        args_schema=None,
    )
