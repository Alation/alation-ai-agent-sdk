from typing import Any, Optional
from alation_ai_agent_sdk import AlationAIAgentSDK
from alation_ai_agent_sdk.lineage import (
    LineageBatchSizeType,
    LineageDesignTimeType,
    LineageDirectionType,
    LineageExcludedSchemaIdsType,
    LineageGraphProcessingType,
    LineageOTypeFilterType,
    LineagePagination,
    LineageRootNode,
    LineageTimestampType,
)
from langchain.tools import StructuredTool


def get_alation_context_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    alation_context_tool = sdk.context_tool

    def run_with_signature(question: str, signature: dict[str, Any] | None = None):
        return alation_context_tool.run(question=question, signature=signature)

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
        if "signature" in kwargs:
            signature = kwargs["signature"]

        # Pattern 2: direct dict without signature keyword
        elif "args" in kwargs and kwargs["args"]:
            signature = kwargs["args"][0]

        # Pattern 3: Positional argument
        elif args and len(args) > 0:
            signature = args[0]

        # Case 4: No signature provided
        else:
            signature = None

        result = bulk_retrieval_tool.run(signature=signature)
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


def get_update_catalog_asset_metadata_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    update_tool = sdk.update_catalog_asset_metadata_tool

    def run_with_args(*args, **kwargs):
        # Accepts either custom_field_values as a keyword or as the first positional argument
        if "custom_field_values" in kwargs:
            custom_field_values = kwargs["custom_field_values"]
        elif args:
            custom_field_values = args[0]
        else:
            raise TypeError("custom_field_values argument is required")
        return update_tool.run(custom_field_values=custom_field_values)

    return StructuredTool.from_function(
        name=update_tool.name,
        description=update_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_check_job_status_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    check_job_status_tool = sdk.check_job_status_tool

    def run_with_args(job_id: int):
        return check_job_status_tool.run(job_id=job_id)

    return StructuredTool.from_function(
        name=check_job_status_tool.name,
        description=check_job_status_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_generate_data_product_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    generate_data_product_tool = sdk.generate_data_product_tool

    def run_with_no_args():
        return generate_data_product_tool.run()

    return StructuredTool.from_function(
        name=generate_data_product_tool.name,
        description=generate_data_product_tool.description,
        func=run_with_no_args,
    )


def get_alation_lineage_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    lineage_tool = sdk.lineage_tool

    def run_with_args(
        root_node: LineageRootNode,
        direction: LineageDirectionType,
        limit: Optional[int] = 1000,
        batch_size: Optional[LineageBatchSizeType] = 1000,
        pagination: Optional[LineagePagination] = None,
        processing_mode: Optional[LineageGraphProcessingType] = None,
        show_temporal_objects: Optional[bool] = False,
        design_time: Optional[LineageDesignTimeType] = None,
        max_depth: Optional[int] = 10,
        excluded_schema_ids: Optional[LineageExcludedSchemaIdsType] = None,
        allowed_otypes: Optional[LineageOTypeFilterType] = None,
        time_from: Optional[LineageTimestampType] = None,
        time_to: Optional[LineageTimestampType] = None,
    ):
        return lineage_tool.run(
            root_node=root_node,
            direction=direction,
            limit=limit,
            batch_size=batch_size,
            pagination=pagination,
            processing_mode=processing_mode,
            show_temporal_objects=show_temporal_objects,
            design_time=design_time,
            max_depth=max_depth,
            excluded_schema_ids=excluded_schema_ids,
            allowed_otypes=allowed_otypes,
            time_from=time_from,
            time_to=time_to,
        )

    return StructuredTool.from_function(
        name=lineage_tool.name,
        description=lineage_tool.description,
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


def get_custom_fields_definitions_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    custom_fields_definitions_tool = sdk.get_custom_fields_definitions_tool

    def run_with_no_args():
        return custom_fields_definitions_tool.run()

    return StructuredTool.from_function(
        name=custom_fields_definitions_tool.name,
        description=custom_fields_definitions_tool.description,
        func=run_with_no_args,
        args_schema=None,
    )


def get_data_dictionary_instructions_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_dict_tool = sdk.get_data_dictionary_instructions_tool

    def run_with_no_args():
        return data_dict_tool.run()

    return StructuredTool.from_function(
        name=data_dict_tool.name,
        description=data_dict_tool.description,
        func=run_with_no_args,
        args_schema=None,
    )
