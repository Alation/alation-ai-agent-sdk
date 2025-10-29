from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

from alation_ai_agent_sdk.errors import AlationAPIError
from .api import (
    AlationAPI,
    AuthParams,
    CatalogAssetMetadataPayloadItem,
)
from .tools import (
    AlationContextTool,
    AlationBulkRetrievalTool,
    AlationGetDataProductTool,
    AlationLineageTool,
    UpdateCatalogAssetMetadataTool,
    CheckJobStatusTool,
    CheckDataQualityTool,
    GenerateDataProductTool,
    GetCustomFieldsDefinitionsTool,
    GetDataDictionaryInstructionsTool,
    SignatureCreationTool,
    AnalyzeCatalogQuestionTool,
    BiReportSearchTool,
    BiReportAgentTool,
    CatalogContextSearchAgentTool,
    CatalogSearchAgentTool,
    ChartCreateAgentTool,
    DataProductQueryAgentTool,
    DeepResearchAgentTool,
    QueryFlowAgentTool,
    SqlQueryAgentTool,
    SqlExecutionTool,
    GenerateChartFromSqlAndCodeTool,
    GetDataSchemaTool,
    GetDataSourcesTool,
    ListDataProductsTool,
    SearchCatalogTool,
    GetSearchFilterFieldsTool,
    GetSearchFilterValuesTool,
    CustomAgentTool,
)
from .lineage import (
    LineageToolResponse,
    make_lineage_kwargs,
    LineageRootNode,
    LineageDirectionType,
    LineageDesignTimeType,
    LineageGraphProcessingType,
    LineageExcludedSchemaIdsType,
    LineageOTypeFilterType,
    LineageTimestampType,
    LineagePagination,
    LineageBatchSizeType,
)


class AlationTools:
    # Tools
    AGGREGATED_CONTEXT = "aggregated_context"
    ANALYZE_CATALOG_QUESTION = "analyze_catalog_question"
    BI_REPORT_SEARCH = "bi_report_search"
    BULK_RETRIEVAL = "bulk_retrieval"
    CATALOG_SEARCH = "catalog_search"
    CHART_CREATE_AGENT = "chart_create_agent"
    CHECK_JOB_STATUS = "check_job_status"
    DATA_QUALITY = "data_quality"
    GENERATE_CHART_FROM_SQL_AND_CODE = "generate_chart_from_sql_and_code"
    GENERATE_DATA_PRODUCT = "generate_data_product"
    GET_CUSTOM_FIELDS_DEFINITIONS = "get_custom_fields_definitions"
    GET_DATA_DICTIONARY_INSTRUCTIONS = "get_data_dictionary_instructions"
    GET_DATA_PRODUCT = "data_product"  # TODO: jags thinks this may be broken
    GET_DATA_SCHEMA = "get_data_schema"
    GET_DATA_SOURCES = "get_data_sources"
    GET_SEARCH_FILTER_FIELDS = "get_search_filter_fields"
    GET_SEARCH_FILTER_VALUES = "get_search_filter_values"
    LINEAGE = "lineage"
    LIST_DATA_PRODUCTS = "list_data_products"
    SIGNATURE_CREATION = "signature_creation"
    SQL_EXECUTION = "sql_execution"
    UPDATE_METADATA = "update_metadata"
    # Agents
    BI_REPORT_AGENT = "bi_report_agent"
    CATALOG_CONTEXT_SEARCH_AGENT = "catalog_context_search_agent"
    CATALOG_SEARCH_AGENT = "catalog_search_agent"
    CUSTOM_AGENT = "custom_agent"
    DATA_PRODUCT_QUERY_AGENT = "data_product_query_agent"
    DEEP_RESEARCH_AGENT = "deep_research_agent"
    QUERY_FLOW_AGENT = "query_flow_agent"
    SQL_QUERY_AGENT = "sql_query_agent"


class AgentSDKOptions:
    def __init__(
        self,
        skip_instance_info: Optional[bool] = False,
        enable_streaming: Optional[bool] = False,
        decode_nested_json: Optional[bool] = True,
        # TBD: option for only preserver content from part instead of whole response
    ):
        self.skip_instance_info = skip_instance_info
        self.enable_streaming = enable_streaming
        self.decode_nested_json = decode_nested_json
        # TBD: decide on stripping extra metadata from streamed response for non-streaming cases?
        # TBD: another parameter for whether to allow tools that output html


class AlationAIAgentSDK:
    """
    SDK for interacting with Alation AI Agent capabilities.

    Can be initialized using Service Account authentication.
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", auth_method="service_account", auth_params=("your_client_id", "your_client_secret"))
    """

    def __init__(
        self,
        base_url: str,
        auth_method: str,
        auth_params: AuthParams,
        enabled_tools: Optional[set[str]] = None,
        disabled_tools: Optional[set[str]] = None,
        enabled_beta_tools: Optional[set[str]] = None,
        dist_version: Optional[str] = None,
        sdk_options: Optional[AgentSDKOptions] = None,
    ):
        if sdk_options is None:
            sdk_options = AgentSDKOptions()
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")

        if not auth_method or not isinstance(auth_method, str):
            raise ValueError("auth_method must be a non-empty string.")

        self.enabled_tools = enabled_tools or set()
        self.disabled_tools = disabled_tools or set()
        self.enabled_beta_tools = enabled_beta_tools or set()
        self.options = sdk_options

        # Delegate validation of auth_params to AlationAPI
        self.api = AlationAPI(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=auth_params,
            dist_version=dist_version,
            skip_instance_info=sdk_options.skip_instance_info,
            enable_streaming=sdk_options.enable_streaming,
            decode_nested_json=sdk_options.decode_nested_json,
        )
        self.context_tool = AlationContextTool(self.api)
        self.bulk_retrieval_tool = AlationBulkRetrievalTool(self.api)
        self.data_product_tool = AlationGetDataProductTool(self.api)
        self.update_catalog_asset_metadata_tool = UpdateCatalogAssetMetadataTool(
            self.api
        )
        self.check_job_status_tool = CheckJobStatusTool(self.api)
        self.generate_data_product_tool = GenerateDataProductTool(self.api)
        self.lineage_tool = AlationLineageTool(self.api)
        self.check_data_quality_tool = CheckDataQualityTool(self.api)
        self.get_custom_fields_definitions_tool = GetCustomFieldsDefinitionsTool(
            self.api
        )
        self.get_data_dictionary_instructions_tool = GetDataDictionaryInstructionsTool(
            self.api
        )
        self.signature_creation_tool = SignatureCreationTool(self.api)
        self.analyze_catalog_question_tool = AnalyzeCatalogQuestionTool(self.api)
        self.bi_report_search_tool = BiReportSearchTool(self.api)
        self.bi_report_agent_tool = BiReportAgentTool(self.api)
        self.catalog_context_search_agent_tool = CatalogContextSearchAgentTool(self.api)
        self.catalog_search_agent_tool = CatalogSearchAgentTool(self.api)
        self.chart_create_agent_tool = ChartCreateAgentTool(self.api)
        self.data_product_query_agent_tool = DataProductQueryAgentTool(self.api)
        self.deep_research_agent_tool = DeepResearchAgentTool(self.api)
        self.query_flow_agent_tool = QueryFlowAgentTool(self.api)
        self.sql_query_agent_tool = SqlQueryAgentTool(self.api)
        self.sql_execution_tool = SqlExecutionTool(self.api)
        self.generate_chart_from_sql_and_code_tool = GenerateChartFromSqlAndCodeTool(
            self.api
        )
        self.get_data_schema_tool = GetDataSchemaTool(self.api)
        self.get_data_sources_tool = GetDataSourcesTool(self.api)
        self.list_data_products_tool = ListDataProductsTool(self.api)
        self.search_catalog_tool = SearchCatalogTool(self.api)
        self.get_search_filter_fields_tool = GetSearchFilterFieldsTool(self.api)
        self.get_search_filter_values_tool = GetSearchFilterValuesTool(self.api)
        self.custom_agent_tool = CustomAgentTool(self.api)

    BETA_TOOLS = {AlationTools.LINEAGE}

    def get_context(
        self, question: str, signature: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch context from Alation's catalog for a given question and signature.

        Returns either:
        - JSON context result (dict)
        - Error object with keys: message, reason, resolution_hint, response_body
        """
        return self.context_tool.run(question=question, signature=signature)

    def get_bulk_objects(self, signature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch bulk objects from Alation's catalog based on signature specifications.

        Args:
            signature (Dict[str, Any]): A signature defining object types, fields, and filters.

        Returns:
            Dict[str, Any]: Contains the catalog objects matching the signature criteria.

        Example signature:
            {
                "table": {
                    "fields_required": ["name", "title", "description", "url"],
                    "search_filters": {
                        "flags": ["Endorsement"]
                    },
                    "limit": 100
                }
            }
        """
        return self.bulk_retrieval_tool.run(signature=signature)

    def get_data_products(
        self, product_id: Optional[str] = None, query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch data products from Alation's catalog for a given product_id or user query.

        Args:
            product_id (str, optional): A product id string for direct lookup.
            query (str, optional): A free-text search query (e.g., "customer churn") to find relevant data products.
            At least one must be provided.

        Returns:
            Dict[str, Any]: Contains 'instructions' (string) and 'results' (list of data product dicts).

        Raises:
            ValueError: If neither product_id nor query is provided.
            AlationAPIError: On network, API, or response errors.
        """
        return self.data_product_tool.run(product_id=product_id, query=query)

    def get_lineage(
        self,
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
    ) -> LineageToolResponse:
        """
        Fetch lineage information from Alation's catalog for a given object / root node.

        Args:
            root_node (LineageRootNode): The root node to start lineage from.
            direction (LineageDirectionType): The direction of lineage to fetch, either "upstream" or "downstream".
            limit (int, optional): The maximum number of nodes to return. Defaults to 1000.
            batch_size (int, optional): The size of each batch for chunked processing. Defaults to 1000.
            pagination (LineagePagination, optional): Pagination parameters only used with chunked processing.
            processing_mode (LineageGraphProcessingType, optional): The processing mode for lineage graph. Strongly recommended to use 'complete' for full lineage graphs.
            show_temporal_objects (bool, optional): Whether to include temporary objects in the lineage. Defaults to False.
            design_time (LineageDesignTimeType, optional): The design time option to filter lineage. Defaults to LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME.
            max_depth (int, optional): The maximum depth to traverse in the lineage graph. Defaults to 10.
            excluded_schema_ids (LineageExcludedSchemaIdsType, optional): A list of excluded schema IDs to filter lineage nodes. Defaults to None.
            allowed_otypes (LineageOTypeFilterType, optional): A list of allowed object types to filter lineage nodes. Defaults to None.
            time_from (LineageTimestampType, optional): The start time for temporal lineage filtering. Defaults to None.
            time_to (LineageTimestampType, optional): The end time for temporal lineage filtering. Defaults to None.

        Returns:
            Dict[str, Dict[str, any]]]: A dictionary containing the lineage `graph` and `pagination` information.

        Raises:
            ValueError: When argument combinations are invalid, such as:
                pagination in complete processing mode,
                allowed_otypes in chunked processing mode
            AlationAPIError: On network, API, or response errors.
        """
        lineage_kwargs = make_lineage_kwargs(
            root_node=root_node,
            processing_mode=processing_mode,
            show_temporal_objects=show_temporal_objects,
            design_time=design_time,
            max_depth=max_depth,
            excluded_schema_ids=excluded_schema_ids,
            allowed_otypes=allowed_otypes,
            time_from=time_from,
            time_to=time_to,
        )
        return self.api.get_bulk_lineage(
            root_nodes=[root_node],
            direction=direction,
            limit=limit,
            batch_size=batch_size,
            pagination=pagination,
            **lineage_kwargs,
        )

    def update_catalog_asset_metadata(
        self, custom_field_values: list[CatalogAssetMetadataPayloadItem]
    ) -> dict:
        """
        Updates metadata for one or more Alation catalog assets.

        Args:
            custom_field_values (list[CatalogAssetMetadataPayloadItem]): List of payload items for updating catalog asset metadata.
                Each item must have the following structure:

                CatalogAssetMetadataPayloadItem = TypedDict('CatalogAssetMetadataPayloadItem', {
                    'otype': Literal['glossary_v3', 'glossary_term'],  # Only these otypes are supported
                    'oid': int,  # The object ID of the asset to update
                    'field_id': Literal[3, 4],  # 3 for TEXT, 4 for RICH_TEXT
                    'value': Any,  # The value to set for the field. Type is validated by field_id -> type mapping.
                })
                Example:
                    {
                        "oid": 219,
                        "otype": "glossary_term",
                        "field_id": 3,
                        "value": "New Title"
                    }

        Returns:
            dict: One of the following:
                - On success: {"job_id": <int>} (job is queued, use get_job_status to track progress)
                - On error: {
                      "title": "Invalid Payload",
                      "detail": "Please check the API documentation for more details on the spec.",
                      "errors": [ ... ],
                      "code": "400000"
                  }
        """
        return self.update_catalog_asset_metadata_tool.run(
            custom_field_values=custom_field_values
        )

    def check_job_status(self, job_id: int) -> dict:
        """
        Check the status of a bulk metadata job in Alation by job ID.

        Args:
            job_id (int): The integer job identifier returned by a previous bulk operation.

        Returns:
            dict: The API response containing job status and details.
        """
        return self.check_job_status_tool.run(job_id=job_id)

    def check_data_quality(
        self,
        table_ids: Optional[list] = None,
        sql_query: Optional[str] = None,
        db_uri: Optional[str] = None,
        ds_id: Optional[int] = None,
        bypassed_dq_sources: Optional[list] = None,
        default_schema_name: Optional[str] = None,
        output_format: Optional[str] = None,
        dq_score_threshold: Optional[int] = None,
    ) -> Union[Dict[str, Any], str]:
        """
        Check SQL Query or tables for quality using Alation's Data Quality API.
        Returns dict (JSON) or str (YAML Markdown) depending on output_format.
        """
        if not table_ids and not sql_query:
            raise ValueError(
                "At least one of 'table_ids' or 'sql_query' must be provided."
            )

        try:
            return self.check_data_quality_tool.run(
                table_ids=table_ids,
                sql_query=sql_query,
                db_uri=db_uri,
                ds_id=ds_id,
                bypassed_dq_sources=bypassed_dq_sources,
                default_schema_name=default_schema_name,
                output_format=output_format,
                dq_score_threshold=dq_score_threshold,
            )
        except AlationAPIError as e:
            return {"error": e.to_dict()}

    def generate_data_product(self) -> str:
        """
        Generate complete instructions for creating Alation Data Products.

        Returns a comprehensive guide including:
        - The current Alation Data Product schema
        - A validated example following the schema
        - Detailed instructions for converting user input to valid YAML

        Returns:
            str: Complete instruction set for data product creation
        """
        return self.generate_data_product_tool.run()

    def get_custom_fields_definitions(self) -> Dict[str, Any]:
        """
        Retrieve all custom field definitions from the Alation instance.

        Custom fields are user-defined metadata fields. This method requires admin permissions.
        """
        return self.get_custom_fields_definitions_tool.run()

    def get_data_dictionary_instructions(self) -> str:
        """
        Generate comprehensive instructions for creating data dictionary CSV files.

        Returns:
            Complete instruction set for data dictionary CSV generation
        """
        return self.get_data_dictionary_instructions_tool.run()

    def get_signature_creation_instructions(self) -> str:
        """
        Returns comprehensive instructions for creating the signature parameter for alation_context
        and bulk_retrieval tools.

        Returns:
        Comprehensive signature creation instructions including:
            - Basic structure patterns
            - Object types and fields reference
            - Field inclusion logic
            - Parameter specifications
            - Decision workflow
            - Validation rules
        """
        return self.signature_creation_tool.run()

    def analyze_catalog_question(self, question: str) -> str:
        """
        Analyze a catalog question and return workflow guidance.

        PRIMARY ENTRY POINT for LLM agents. Analyzes the question and provides
        step-by-step instructions for answering it using other tools.

        Args:
            question (str): Natural language question about the data catalog

        Returns:
            str: Formatted workflow instructions including
        """
        return self.analyze_catalog_question_tool.run(question=question)

    def search_bi_reports(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search over the Alation catalog to find BI report objects.

        Args:
            search_term (str): Search term to filter BI reports by name
            limit (int, optional): Maximum number of results to return (default: 20, max: 100)

        Returns:
            Dict[str, Any]: List of BI report objects that match the search query parameters
        """
        return self.bi_report_search_tool.run(search_term=search_term, limit=limit)

    def bi_report_agent(self, message: str) -> Dict[str, Any]:
        """
        BI Report Agent for searching and analyzing BI report objects.

        Args:
            message (str): Natural language message describing what you're looking for

        Returns:
            Dict[str, Any]: Detailed information about BI reports matching your request
        """
        return self.bi_report_agent_tool.run(message=message)

    def catalog_context_search_agent(self, message: str) -> Dict[str, Any]:
        """
        Catalog Context Search Agent for searching catalog objects with enhanced context.

        Args:
            message (str): Natural language description of what you're searching for

        Returns:
            Dict[str, Any]: Contextually-aware search results with enhanced metadata and relationships
        """
        return self.catalog_context_search_agent_tool.run(message=message)

    def catalog_search_agent(self, message: str) -> Dict[str, Any]:
        """
        Catalog Search Agent for general catalog search operations.

        Args:
            message (str): Natural language search query

        Returns:
            Dict[str, Any]: Search results from the data catalog matching your query
        """
        return self.catalog_search_agent_tool.run(message=message)

    def chart_create_agent(self, message: str) -> Dict[str, Any]:
        """
        Chart Create Agent for creating charts and visualizations.

        Args:
            message (str): Description of the chart or visualization you want to create

        Returns:
            Dict[str, Any]: Chart creation guidance, code, or visualization assets
        """
        return self.chart_create_agent_tool.run(message=message)

    def data_product_query_agent(
        self, message: str, data_product_id: str, auth_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Data Product Query Agent for querying data products.

        Args:
            message (str): Your query or request related to the data product
            data_product_id (str): The ID of the data product to work with
            auth_id (str, optional): Authentication ID for data access

        Returns:
            Dict[str, Any]: Query results, analysis, or guidance specific to the requested data product
        """
        return self.data_product_query_agent_tool.run(
            message=message, data_product_id=data_product_id, auth_id=auth_id
        )

    def deep_research_agent(self, message: str) -> Dict[str, Any]:
        """
        Deep Research Agent for comprehensive research tasks.

        Args:
            message (str): Research question or topic you want to investigate

        Returns:
            Dict[str, Any]: Comprehensive research results with detailed analysis and insights
        """
        return self.deep_research_agent_tool.run(message=message)

    def query_flow_agent(self, message: str) -> Dict[str, Any]:
        """
        Query Flow Agent for SQL query workflow management.

        Args:
            message (str): Description of your query workflow needs

        Returns:
            Dict[str, Any]: Query workflow guidance, optimization suggestions, and execution plans
        """
        return self.query_flow_agent_tool.run(message=message)

    def sql_query_agent(self, message: str) -> Dict[str, Any]:
        """
        SQL Query Agent for SQL query generation and analysis.

        Args:
            message (str): Description of the data you need or SQL task

        Returns:
            Dict[str, Any]: SQL queries, query analysis, optimization suggestions, and execution guidance
        """
        return self.sql_query_agent_tool.run(message=message)

    def execute_sql(
        self,
        data_product_id: str,
        sql: str,
        result_table_name: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute SQL queries within a data product context.

        Args:
            data_product_id (str): The ID of the data product to execute queries against
            sql (str): The SQL query to execute
            result_table_name (str): Name for the result table
            pre_exec_sql (str, optional): SQL to execute before the main query
            auth_id (str, optional): Authentication ID for data access

        Returns:
            Dict[str, Any]: Query execution results including data and metadata
        """
        return self.sql_execution_tool.run(
            data_product_id=data_product_id,
            sql=sql,
            result_table_name=result_table_name,
            pre_exec_sql=pre_exec_sql,
            auth_id=auth_id,
        )

    def generate_chart_from_sql_and_code(
        self,
        data_product_id: str,
        sql: str,
        chart_code_snippet: str,
        image_title: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate charts from SQL queries and code snippets within a data product context.

        Args:
            data_product_id (str): The ID of the data product to work with
            sql (str): The SQL query to fetch data
            chart_code_snippet (str): Code snippet for generating the chart
            image_title (str): Title for the generated chart image
            pre_exec_sql (str, optional): SQL to execute before the main query
            auth_id (str, optional): Authentication ID for data access

        Returns:
            Dict[str, Any]: Generated chart data and visualization assets
        """
        return self.generate_chart_from_sql_and_code_tool.run(
            data_product_id=data_product_id,
            sql=sql,
            chart_code_snippet=chart_code_snippet,
            image_title=image_title,
            pre_exec_sql=pre_exec_sql,
            auth_id=auth_id,
        )

    def get_data_schema(
        self,
        data_product_id: str,
        pre_exec_sql: Optional[str] = None,
        auth_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve data schema information for a data product.

        Args:
            data_product_id (str): The ID of the data product to get schema for
            pre_exec_sql (str, optional): SQL to execute before schema retrieval
            auth_id (str, optional): Authentication ID for data access

        Returns:
            Dict[str, Any]: Data schema information including table structures and metadata
        """
        return self.get_data_schema_tool.run(
            data_product_id=data_product_id, pre_exec_sql=pre_exec_sql, auth_id=auth_id
        )

    def get_data_sources(self, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve available data sources from the catalog.

        Args:
            limit (int, optional): Maximum number of data sources to return (default: 100)

        Returns:
            Dict[str, Any]: List of available data sources with their metadata and connection information
        """
        return self.get_data_sources_tool.run(limit=limit)

    def list_data_products(
        self, search_term: str, limit: int = 5, marketplace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List data products based on search criteria.

        Args:
            search_term (str): Search term to filter data products
            limit (int, optional): Maximum number of results to return (default: 5)
            marketplace_id (str, optional): ID of the marketplace to search in

        Returns:
            Dict[str, Any]: List of data products matching the search criteria
        """
        return self.list_data_products_tool.run(
            search_term=search_term, limit=limit, marketplace_id=marketplace_id
        )

    def search_catalog(
        self,
        search_term: str,
        object_types: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search the catalog for objects matching specified criteria.

        Args:
            search_term (str): Search term to match against catalog objects
            object_types (List[str], optional): List of object types to filter by
            filters (Dict[str, Any], optional): Additional filters to apply to the search

        Returns:
            Dict[str, Any]: Search results matching the specified criteria with object metadata
        """
        return self.search_catalog_tool.run(
            search_term=search_term, object_types=object_types, filters=filters
        )

    def get_search_filter_fields(
        self, search_term: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get available search filter fields for catalog search.

        Args:
            search_term (str): Search term to match against filter field names
            limit (int, optional): Maximum number of filter fields to return (default: 10)

        Returns:
            Dict[str, Any]: List of available search filter fields with their metadata
        """
        return self.get_search_filter_fields_tool.run(
            search_term=search_term, limit=limit
        )

    def get_search_filter_values(
        self, field_id: int, search_term: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get available values for a specific search filter field.

        Args:
            field_id (int): ID of the filter field to get values for
            search_term (str): Search term to match against filter values
            limit (int, optional): Maximum number of filter values to return (default: 10)

        Returns:
            Dict[str, Any]: List of available values for the specified filter field
        """
        return self.get_search_filter_values_tool.run(
            field_id=field_id, search_term=search_term, limit=limit
        )

    def execute_custom_agent(
        self, agent_config_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a custom agent configuration by its UUID.

        Args:
            agent_config_id (str): The UUID of the agent configuration to use
            payload (Dict[str, Any]): The payload to send to the agent. Must conform
                to the agent's specific input JSON schema

        Returns:
            Dict[str, Any]: Agent response based on the specific agent's capabilities

        Example:
            execute_custom_agent(
                agent_config_id="550e8400-e29b-41d4-a716-446655440000",
                payload={"message": "Analyze this data"}
            )
        """
        return self.custom_agent_tool.run(
            agent_config_id=agent_config_id, payload=payload
        )

    def get_tools(self):
        from .utils import is_tool_enabled

        tools = []
        if is_tool_enabled(
            AlationTools.AGGREGATED_CONTEXT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.context_tool)
        if is_tool_enabled(
            AlationTools.BULK_RETRIEVAL,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.bulk_retrieval_tool)
        if is_tool_enabled(
            AlationTools.GET_DATA_PRODUCT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.data_product_tool)
        if is_tool_enabled(
            AlationTools.UPDATE_METADATA,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.update_catalog_asset_metadata_tool)
        if is_tool_enabled(
            AlationTools.CHECK_JOB_STATUS,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.check_job_status_tool)
        if is_tool_enabled(
            AlationTools.LINEAGE,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.lineage_tool)
        if is_tool_enabled(
            AlationTools.DATA_QUALITY,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.check_data_quality_tool)
        if is_tool_enabled(
            AlationTools.GENERATE_DATA_PRODUCT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.generate_data_product_tool)
        if is_tool_enabled(
            AlationTools.GET_CUSTOM_FIELDS_DEFINITIONS,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_custom_fields_definitions_tool)
        if is_tool_enabled(
            AlationTools.GET_DATA_DICTIONARY_INSTRUCTIONS,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_data_dictionary_instructions_tool)
        if is_tool_enabled(
            AlationTools.SIGNATURE_CREATION,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.signature_creation_tool)
        if is_tool_enabled(
            AlationTools.ANALYZE_CATALOG_QUESTION,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.analyze_catalog_question_tool)
        if is_tool_enabled(
            AlationTools.BI_REPORT_SEARCH,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.bi_report_search_tool)
        if is_tool_enabled(
            AlationTools.BI_REPORT_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.bi_report_agent_tool)
        if is_tool_enabled(
            AlationTools.CATALOG_CONTEXT_SEARCH_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.catalog_context_search_agent_tool)
        if is_tool_enabled(
            AlationTools.CATALOG_SEARCH_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.catalog_search_agent_tool)
        if is_tool_enabled(
            AlationTools.CATALOG_SEARCH,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.search_catalog_tool)
        if is_tool_enabled(
            AlationTools.CHART_CREATE_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.chart_create_agent_tool)
        if is_tool_enabled(
            AlationTools.DATA_PRODUCT_QUERY_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.data_product_query_agent_tool)
        if is_tool_enabled(
            AlationTools.DEEP_RESEARCH_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.deep_research_agent_tool)
        if is_tool_enabled(
            AlationTools.GENERATE_CHART_FROM_SQL_AND_CODE,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.generate_chart_from_sql_and_code_tool)
        if is_tool_enabled(
            AlationTools.GET_DATA_SCHEMA,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_data_schema_tool)
        if is_tool_enabled(
            AlationTools.GET_DATA_SOURCES,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_data_sources_tool)
        if is_tool_enabled(
            AlationTools.GET_SEARCH_FILTER_FIELDS,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_search_filter_fields_tool)
        if is_tool_enabled(
            AlationTools.GET_SEARCH_FILTER_VALUES,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.get_search_filter_values_tool)
        if is_tool_enabled(
            AlationTools.LIST_DATA_PRODUCTS,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.list_data_products_tool)
        if is_tool_enabled(
            AlationTools.QUERY_FLOW_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.query_flow_agent_tool)
        if is_tool_enabled(
            AlationTools.SQL_QUERY_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.sql_query_agent_tool)
        if is_tool_enabled(
            AlationTools.SQL_EXECUTION,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.sql_execution_tool)
        if is_tool_enabled(
            AlationTools.CUSTOM_AGENT,
            self.enabled_tools,
            self.disabled_tools,
            self.enabled_beta_tools,
        ):
            tools.append(self.custom_agent_tool)
        return tools
