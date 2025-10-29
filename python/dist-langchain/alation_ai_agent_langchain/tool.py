from typing import Any, Optional
from alation_ai_agent_sdk import AlationAIAgentSDK
from alation_ai_agent_sdk.types import Filter
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

    def run_with_signature(
        question: str,
        signature: dict[str, Any] | None = None,
        chat_id: Optional[str] = None,
    ):
        return alation_context_tool.run(
            question=question, signature=signature, chat_id=chat_id
        )

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
        chat_id = kwargs.get("chat_id", None)

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

        result = bulk_retrieval_tool.run(signature=signature, chat_id=chat_id)
        return result

    return StructuredTool.from_function(
        name=bulk_retrieval_tool.name,
        description=bulk_retrieval_tool.description,
        func=run_with_signature,
        args_schema=None,
    )


def get_alation_data_products_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_products_tool = sdk.data_product_tool

    def run_with_args(
        product_id: Optional[str] = None,
        query: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return data_products_tool.run(
            product_id=product_id, query=query, chat_id=chat_id
        )

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

    def run_with_args(chat_id: Optional[str] = None):
        return custom_fields_definitions_tool.run(chat_id=chat_id)

    return StructuredTool.from_function(
        name=custom_fields_definitions_tool.name,
        description=custom_fields_definitions_tool.description,
        func=run_with_args,
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


def get_signature_creation_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    signature_creation_tool = sdk.signature_creation_tool

    def run_with_args(chat_id: Optional[str] = None):
        return signature_creation_tool.run(chat_id=chat_id)

    return StructuredTool.from_function(
        name=signature_creation_tool.name,
        description=signature_creation_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_analyze_catalog_question_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    analyze_tool = sdk.analyze_catalog_question_tool

    def run_with_question(question: str, chat_id: Optional[str] = None):
        return analyze_tool.run(question=question, chat_id=chat_id)

    return StructuredTool.from_function(
        name=analyze_tool.name,
        description=analyze_tool.description,
        func=run_with_question,
        args_schema=None,
    )


def get_bi_report_search_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    bi_report_search_tool = sdk.bi_report_search_tool

    def run_with_args(search_term: str, limit: int = 20, filters: Optional[list[Filter]] = None, chat_id: Optional[str] = None):
        return bi_report_search_tool.run(
            search_term=search_term, limit=limit, filters=filters, chat_id=chat_id
        )

    return StructuredTool.from_function(
        name=bi_report_search_tool.name,
        description=bi_report_search_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_bi_report_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    bi_report_agent_tool = sdk.bi_report_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return bi_report_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=bi_report_agent_tool.name,
        description=bi_report_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_catalog_context_search_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    catalog_context_search_agent_tool = sdk.catalog_context_search_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return catalog_context_search_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=catalog_context_search_agent_tool.name,
        description=catalog_context_search_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_catalog_search_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    catalog_search_agent_tool = sdk.catalog_search_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return catalog_search_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=catalog_search_agent_tool.name,
        description=catalog_search_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_chart_create_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    chart_create_agent_tool = sdk.chart_create_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return chart_create_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=chart_create_agent_tool.name,
        description=chart_create_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_custom_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    custom_agent_tool = sdk.custom_agent_tool

    def run_with_args(
        agent_config_id: str, payload: dict[str, Any], chat_id: Optional[str] = None
    ):
        return custom_agent_tool.run(
            agent_config_id=agent_config_id, payload=payload, chat_id=chat_id
        )

    return StructuredTool.from_function(
        name=custom_agent_tool.name,
        description=custom_agent_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_data_product_query_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_product_query_agent_tool = sdk.data_product_query_agent_tool

    def run_with_args(
        message: str,
        data_product_id: str,
        auth_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return data_product_query_agent_tool.run(
            message=message,
            data_product_id=data_product_id,
            auth_id=auth_id,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=data_product_query_agent_tool.name,
        description=data_product_query_agent_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_deep_research_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    deep_research_agent_tool = sdk.deep_research_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return deep_research_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=deep_research_agent_tool.name,
        description=deep_research_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_generate_chart_from_sql_and_code_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    generate_chart_tool = sdk.generate_chart_from_sql_and_code_tool

    def run_with_args(
        data_product_id: str,
        sql: str,
        chart_code_snippet: str,
        image_title: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return generate_chart_tool.run(
            data_product_id=data_product_id,
            sql=sql,
            chart_code_snippet=chart_code_snippet,
            image_title=image_title,
            pre_exec_sql=pre_exec_sql,
            auth_id=auth_id,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=generate_chart_tool.name,
        description=generate_chart_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_data_schema_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_schema_tool = sdk.get_data_schema_tool

    def run_with_args(
        data_product_id: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return data_schema_tool.run(
            data_product_id=data_product_id,
            pre_exec_sql=pre_exec_sql,
            auth_id=auth_id,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=data_schema_tool.name,
        description=data_schema_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_data_sources_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    data_sources_tool = sdk.get_data_sources_tool

    def run_with_args(limit: int = 100, chat_id: Optional[str] = None):
        return data_sources_tool.run(limit=limit, chat_id=chat_id)

    return StructuredTool.from_function(
        name=data_sources_tool.name,
        description=data_sources_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_list_data_products_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    list_data_products_tool = sdk.list_data_products_tool

    def run_with_args(
        search_term: str,
        limit: int = 5,
        marketplace_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return list_data_products_tool.run(
            search_term=search_term,
            limit=limit,
            marketplace_id=marketplace_id,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=list_data_products_tool.name,
        description=list_data_products_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_query_flow_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    query_flow_agent_tool = sdk.query_flow_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return query_flow_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=query_flow_agent_tool.name,
        description=query_flow_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )


def get_search_catalog_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    search_catalog_tool = sdk.search_catalog_tool

    def run_with_args(
        search_term: str,
        object_types: Optional[list[str]] = None,
        filters: Optional[list[Filter]] = None,
        chat_id: Optional[str] = None,
    ):
        return search_catalog_tool.run(
            search_term=search_term,
            object_types=object_types,
            filters=filters,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=search_catalog_tool.name,
        description=search_catalog_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_search_filter_fields_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    search_filter_fields_tool = sdk.get_search_filter_fields_tool

    def run_with_args(search_term: str, limit: int = 10, chat_id: Optional[str] = None):
        return search_filter_fields_tool.run(
            search_term=search_term, limit=limit, chat_id=chat_id
        )

    return StructuredTool.from_function(
        name=search_filter_fields_tool.name,
        description=search_filter_fields_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_search_filter_values_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    search_filter_values_tool = sdk.get_search_filter_values_tool

    def run_with_args(
        field_id: int, search_term: str, limit: int = 10, chat_id: Optional[str] = None
    ):
        return search_filter_values_tool.run(
            field_id=field_id, search_term=search_term, limit=limit, chat_id=chat_id
        )

    return StructuredTool.from_function(
        name=search_filter_values_tool.name,
        description=search_filter_values_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_sql_execution_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    sql_execution_tool = sdk.sql_execution_tool

    def run_with_args(
        data_product_id: str,
        sql: str,
        result_table_name: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        return sql_execution_tool.run(
            data_product_id=data_product_id,
            sql=sql,
            result_table_name=result_table_name,
            pre_exec_sql=pre_exec_sql,
            auth_id=auth_id,
            chat_id=chat_id,
        )

    return StructuredTool.from_function(
        name=sql_execution_tool.name,
        description=sql_execution_tool.description,
        func=run_with_args,
        args_schema=None,
    )


def get_sql_query_agent_tool(sdk: AlationAIAgentSDK) -> StructuredTool:
    sql_query_agent_tool = sdk.sql_query_agent_tool

    def run_with_message(message: str, chat_id: Optional[str] = None):
        return sql_query_agent_tool.run(message=message, chat_id=chat_id)

    return StructuredTool.from_function(
        name=sql_query_agent_tool.name,
        description=sql_query_agent_tool.description,
        func=run_with_message,
        args_schema=None,
    )
