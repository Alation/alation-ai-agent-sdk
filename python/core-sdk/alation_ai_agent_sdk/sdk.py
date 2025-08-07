from typing import (
    Any,
    Dict,
    Optional,
    Union,
)
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
    AGGREGATED_CONTEXT = "aggregated_context"
    BULK_RETRIEVAL = "bulk_retrieval"
    CHECK_JOB_STATUS = "check_job_status"
    DATA_PRODUCT = "data_product"
    DATA_QUALITY = "data_quality"
    LINEAGE = "lineage"
    UPDATE_METADATA = "update_metadata"
    GENERATE_DATA_PRODUCT = "generate_data_product"


class AlationAIAgentSDK:
    """
    SDK for interacting with Alation AI Agent capabilities.

    Can be initialized using one of two authentication methods:
    1. User Account Authentication:
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", auth_method="user_account", auth_params=(123, "your_refresh_token"))
    2. Service Account Authentication:
       sdk = AlationAIAgentSDK(base_url="https://company.alationcloud.com", auth_method="service_account", auth_params=("your_client_id", "your_client_secret"))
    """

    def __init__(
        self,
        base_url: str,
        auth_method: str,
        auth_params: AuthParams,
        disabled_tools: Optional[set[str]] = None,
        enabled_beta_tools: Optional[set[str]] = None,
        dist_version: Optional[str] = None,
        skip_instance_info: Optional[bool] = False,
    ):
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")

        if not auth_method or not isinstance(auth_method, str):
            raise ValueError("auth_method must be a non-empty string.")

        self.beta_tools = {AlationTools.LINEAGE}
        self.disabled_tools = disabled_tools or set()
        self.enabled_beta_tools = enabled_beta_tools or set()

        # Delegate validation of auth_params to AlationAPI
        self.api = AlationAPI(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=auth_params,
            dist_version=dist_version,
            skip_instance_info=skip_instance_info,
        )
        self.context_tool = AlationContextTool(self.api)
        self.bulk_retrieval_tool = AlationBulkRetrievalTool(self.api)
        self.data_product_tool = AlationGetDataProductTool(self.api)
        self.update_catalog_asset_metadata_tool = UpdateCatalogAssetMetadataTool(self.api)
        self.check_job_status_tool = CheckJobStatusTool(self.api)
        self.generate_data_product_tool = GenerateDataProductTool(self.api)
        self.lineage_tool = AlationLineageTool(self.api)
        self.check_data_quality_tool = CheckDataQualityTool(self.api)

    def is_tool_enabled(self, tool_name: str) -> bool:
        if tool_name in self.disabled_tools:
            return False
        if tool_name not in self.beta_tools:
            return True
        if tool_name in self.enabled_beta_tools:
            return True
        return False

    def set_enabled_beta_tools(self, tools: set[str]):
        self.enabled_beta_tools = tools

    def set_disabled_tools(self, tools: set[str]):
        self.disabled_tools = tools

    def get_context(
        self, question: str, signature: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch context from Alation's catalog for a given question and signature.

        Returns either:
        - JSON context result (dict)
        - Error object with keys: message, reason, resolution_hint, response_body
        """
        return self.context_tool.run(question, signature)

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
        return self.bulk_retrieval_tool.run(signature)

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
        return self.data_product_tool.run(product_id, query)

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
        return self.update_catalog_asset_metadata_tool.run(custom_field_values)

    def check_job_status(self, job_id: int) -> dict:
        """
        Check the status of a bulk metadata job in Alation by job ID.

        Args:
            job_id (int): The integer job identifier returned by a previous bulk operation.

        Returns:
            dict: The API response containing job status and details.
        """
        return self.check_job_status_tool.run(job_id)

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
            raise ValueError("At least one of 'table_ids' or 'sql_query' must be provided.")

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

    def get_tools(self):
        tools = []
        if self.is_tool_enabled(AlationTools.AGGREGATED_CONTEXT):
            tools.append(self.context_tool)
        if self.is_tool_enabled(AlationTools.BULK_RETRIEVAL):
            tools.append(self.bulk_retrieval_tool)
        if self.is_tool_enabled(AlationTools.DATA_PRODUCT):
            tools.append(self.data_product_tool)
        if self.is_tool_enabled(AlationTools.UPDATE_METADATA):
            tools.append(self.update_catalog_asset_metadata_tool)
        if self.is_tool_enabled(AlationTools.CHECK_JOB_STATUS):
            tools.append(self.check_job_status_tool)
        if self.is_tool_enabled(AlationTools.LINEAGE):
            tools.append(self.lineage_tool)
        if self.is_tool_enabled(AlationTools.DATA_QUALITY):
            tools.append(self.check_data_quality_tool)
        if self.is_tool_enabled(AlationTools.GENERATE_DATA_PRODUCT):
            tools.append(self.generate_data_product_tool)
        return tools
