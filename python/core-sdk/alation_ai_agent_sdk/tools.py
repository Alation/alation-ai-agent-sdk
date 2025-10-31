import re
import logging

from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Union,
)
from alation_ai_agent_sdk.api import (
    AlationAPI,
    AlationAPIError,
    CatalogAssetMetadataPayloadItem,
)
from alation_ai_agent_sdk.lineage import (
    LineageBatchSizeType,
    LineageDesignTimeType,
    LineageExcludedSchemaIdsType,
    LineageTimestampType,
    LineageDirectionType,
    LineageGraphProcessingType,
    LineagePagination,
    LineageRootNode,
    LineageOTypeFilterType,
    LineageToolResponse,
    make_lineage_kwargs,
)

from alation_ai_agent_sdk.data_product import (
    get_example_content,
    get_prompt_instructions,
    get_schema_content,
)

from alation_ai_agent_sdk.data_dict import build_optimized_instructions

from alation_ai_agent_sdk.fields import (
    filter_field_properties,
    get_built_in_fields_structured,
    get_built_in_usage_guide,
)
from alation_ai_agent_sdk.event import track_tool_execution

logger = logging.getLogger(__name__)


def min_alation_version(min_version: str):
    """
    Decorator to enforce minimum Alation version for a tool's run method (inclusive).
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            current_version = getattr(self.api, "alation_release_name", None)
            if current_version is None:
                logger.warning(
                    f"[VersionCheck] Unable to extract Alation version for {self.__class__.__name__}. Required >= {min_version}. Proceeding with caution."
                )
                # Continue execution, do not block
                return func(self, *args, **kwargs)
            if not is_version_supported(current_version, min_version):
                logger.warning(
                    f"[VersionCheck] {self.__class__.__name__} blocked: required >= {min_version}, current = {current_version}"
                )
                return {
                    "error": {
                        "message": f"{self.__class__.__name__} requires Alation version >= {min_version}. Current: {current_version}",
                        "reason": "Unsupported Alation Version",
                        "resolution_hint": f"Upgrade your Alation instance to at least {min_version} to use this tool.",
                        "alation_version": current_version,
                    }
                }
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def is_version_supported(current: str, minimum: str) -> bool:
    """
    Compare Alation version strings (e.g., '2025.1.5' >= '2025.1.2'). Returns True if current >= minimum.
    Handles versions with 2 or 3 components (e.g., '2025.3' or '2025.1.2').
    """

    def parse(ver):
        # Match 2 or 3 component versions: major.minor or major.minor.patch
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", ver)
        if match:
            ver = match.group(1)
        parts = [int(p) for p in ver.split(".")]
        # Normalize to 3 components: pad with zeros
        return tuple(parts + [0] * (3 - len(parts)))

    try:
        return parse(current) >= parse(minimum)
    except Exception:
        return False


class AlationContextTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "alation_context"

    @staticmethod
    def _get_description() -> str:
        return """
    CRITICAL: DO NOT CALL THIS TOOL DIRECTLY
    
    LOW-LEVEL TOOL: Semantic search of Alation's data catalog using natural language.

    You MUST call analyze_catalog_question first to determine workflow.
    USE THIS DIRECTLY ONLY WHEN:
    - User explicitly requests "use alation_context"
    - Following analyze_catalog_question instructions
    - User provides a pre-built signature

    ## WHAT THIS TOOL DOES

    Translates natural language into catalog queries. Returns structured data
    about tables, columns, documentation, queries, and BI objects.

    ## PARAMETERS

    - question (required): Exact user question, unmodified
    - signature (optional): JSON specification of fields/filters
    - chat_id (optional): Chat session identifier for context-aware searches

    For signature structure: call get_signature_creation_instructions()

    ## USE CASES

    ✓ "Find sales-related tables" (concept discovery)
    ✓ "Tables about customer data" (semantic search)
    ✓ "Documentation on data warehouse" (content search)

    ✗ "List ALL tables in schema" → use bulk_retrieval (enumeration)
    ✗ "Get all endorsed tables" → use bulk_retrieval (filter-based list)

    See analyze_catalog_question for workflow orchestration.
    See get_signature_creation_instructions for signature details.
    """

    @min_alation_version("2025.1.2")
    @track_tool_execution()
    def run(
        self,
        *,
        question: str,
        signature: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.alation_context_stream(
                question=question,
                signature=signature,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class AlationGetDataProductTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_data_products"

    @staticmethod
    def _get_description() -> str:
        return """
          Retrieve data products from Alation using direct lookup or search.

          Parameters (provide exactly ONE):

          product_id (optional): Exact product identifier for fast direct retrieval
          query (optional): Natural language search query for discovery and exploration
          IMPORTANT: You must provide either product_id OR query, never both.

          Usage Examples:

          get_data_products(product_id="finance:loan_performance_analytics")
          get_data_products(product_id="sg01")
          get_data_products(product_id="d9e2be09-9b36-4052-8c22-91d1cc7faa53")
          get_data_products(query="customer analytics dashboards")
          get_data_products(query="fraud detection models")
          Returns:
          {
          "instructions": "Context about the results and next steps",
          "results": list of data products
          }

          Response Behavior:

          Single result: Complete product specification with all metadata
          Multiple results: Summary format (name, id, description, url)
          """

    @track_tool_execution()
    def run(self, *, product_id: Optional[str] = None, query: Optional[str] = None):
        try:
            return self.api.get_data_products(product_id=product_id, query=query)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class AlationBulkRetrievalTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "bulk_retrieval"

    @staticmethod
    def _get_description() -> str:
        return """
    CRITICAL: DO NOT CALL THIS TOOL DIRECTLY
    
    LOW-LEVEL TOOL: Direct bulk enumeration of catalog objects with filters.

    You MUST call analyze_catalog_question first to determine workflow.

    USE THIS DIRECTLY ONLY WHEN:
    - User explicitly requests "bulk tool" or "bulk_retrieval"
    - Following instructions from analyze_catalog_question

    ## WHAT THIS TOOL DOES

    Fetches complete sets of catalog objects without semantic search.
    Use for structural enumeration, not concept discovery.

    Supported: table, column, schema, query
    Not supported: documentation objects

    ## PARAMETERS

    - signature (required, JSON):
        For complete signature specification, field options, and filter rules,
        call get_signature_creation_instructions() first.
    - chat_id (optional): Chat session identifier

    ## USE CASES

    ✓ "List ALL tables in finance schema"
    ✓ "Get all endorsed tables from data source 5"
    ✓ "Show tables with PII classification"

    ✗ "Find sales-related tables" → use alation_context (concept discovery)
    ✗ "Tables about customers" → use alation_context (semantic search)

    See get_signature_creation_instructions() for complete usage guide.
    """

    @track_tool_execution()
    def run(
        self,
        *,
        signature: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        if not signature:
            return {
                "error": {
                    "message": "Signature parameter is required for bulk retrieval",
                    "reason": "Missing Required Parameter",
                    "resolution_hint": "Provide a signature specifying object types, fields, and optional filters. See tool description for examples.",
                    "example_signature": {
                        "table": {
                            "fields_required": ["name", "title", "description", "url"],
                            "search_filters": {"flags": ["Endorsement"]},
                            "limit": 10,
                        }
                    },
                }
            }

        try:
            ref = self.api.bulk_retrieval_stream(signature=signature, chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class AlationLineageTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_lineage"

    @staticmethod
    def _get_description() -> str:
        return """Retrieves lineage relationships for data catalog objects. Shows what data flows upstream (sources) or downstream (destinations) from a given object.

        WHEN TO USE:
        Use this tool when users ask about data lineage, data flow, dependencies, impact analysis, or questions like "what feeds into this table?" or "what uses this data?"

        REQUIRED PARAMETERS:
        - root_node: The starting object as {"id": object_id, "otype": "object_type"}
        Example: {"id": 123, "otype": "table"} or {"id": 456, "otype": "attribute"}
        - direction: Either "upstream" (sources/inputs) or "downstream" (destinations/outputs)

        COMMON OPTIONAL PARAMETERS:
        - allowed_otypes: Filter to specific object types like ["table", "attribute"]
        - limit: Maximum nodes to return (default: 1000, max: 1000). Never change this unless the user question explicitly mentions a limit.
        - max_depth: How many levels deep to traverse (default: 10)

        PROCESSING CONTROL:
        - processing_mode: "complete" (default, recommended) or "chunked" for portions of graphs
        - batch_size: Nodes per batch for chunked processing (default: 1000)
        - pagination: Continue from previous chunked response {"cursor": X, "request_id": "...", "batch_size": Y, "has_more": true}

        FILTERING OPTIONS:
        - show_temporal_objects: Include temporary objects (default: false)
        - design_time: Filter by creation time - use 3 for both design & runtime (default), 1 for design-time only, 2 for runtime only
        - excluded_schema_ids: Exclude objects from specific schemas like [1, 2, 3]
        - time_from: Start timestamp for temporal filtering (format: "YYYY-MM-DDTHH:MM:SS")
        - time_to: End timestamp for temporal filtering (format: "YYYY-MM-DDTHH:MM:SS")

        SPECIAL OBJECT TYPES:
        For file, directory, and external objects, use fully qualified names:
        {"id": "filesystem_id.path/to/file", "otype": "file"}

        COMMON EXAMPLES:
        - Find upstream tables: get_lineage(root_node={"id": 123, "otype": "table"}, direction="upstream", allowed_otypes=["table"])
        - Find all downstream objects: get_lineage(root_node={"id": 123, "otype": "table"}, direction="downstream")
        - Column-level lineage: get_lineage(root_node={"id": 456, "otype": "attribute"}, direction="upstream", allowed_otypes=["attribute"])
        - Exclude test schemas: get_lineage(root_node={"id": 123, "otype": "table"}, direction="upstream", excluded_schema_ids=[999, 1000])

        RETURNS:
        {"graph": [list of connected objects with relationships], "direction": "upstream|downstream", "pagination": {...}}

        HANDLING RESPONSES:
        - Skip any temporary nodes unless the user question explicitly mentions them
        - Fully qualified names should be split into their component parts (period separated). The last element is the most specific name.
        """

    @track_tool_execution()
    def run(
        self,
        *,
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

        try:
            return self.api.get_bulk_lineage(
                root_nodes=[root_node],
                direction=direction,
                limit=limit,
                batch_size=batch_size,
                pagination=pagination,
                **lineage_kwargs,
            )
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class UpdateCatalogAssetMetadataTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "update_catalog_asset_metadata"

    @staticmethod
    def _get_description() -> str:
        return """
            Updates metadata for Alation catalog assets by modifying existing objects.

            Supported object types:
            - 'glossary_term': Individual glossary terms (corresponds to document objects)
            - 'glossary_v3': Glossary collections (corresponds to doc-folder objects, i.e., Document Hubs)

            NOTE: If you receive object types as 'document' or 'doc-folder', you must map them as follows:
            - 'document' → 'glossary_term'
            - 'doc-folder' → 'glossary_v3'

            Available fields:
            - field_id 3: Title (plain text)
            - field_id 4: Description (supports rich text/HTML formatting)

            Use this tool to:
            - Update titles and descriptions for existing glossary content
            - Modify glossary terms or glossary collections (glossary_v3)
            - Supports both single and bulk operations

            Don't use this tool for:
            - Creating new objects
            - Reading/retrieving asset data (use context tool instead)
            - Updating other field types

            Parameters:
            - custom_field_values (list): List of objects, each containing:
                * oid (string): Asset's unique identifier  
                * otype (string): Asset type - 'glossary_term' or 'glossary_v3'
                * field_id (int): Field to update - 3 for title, 4 for description
                * value (string): New value to set

            Example usage:
                Single asset:
                [{"oid": "123", "otype": "glossary_term", "field_id": 3, "value": "New Title"}]
                
                Multiple assets:
                [{"oid": 219, "otype": "glossary_v3", "field_id": 4, "value": "Sample Description"},
                {"oid": 220, "otype": "glossary_term", "field_id": 3, "value": "Another Title"}]
            
            Returns:
            - Success: {"job_id": <int>} - Updates processed asynchronously
            - Error: {"title": "Invalid Payload", "errors": [...]}
            
            Track progress via:
            - UI: https://<company>.alationcloud.com/monitor/completed_tasks/
            - TOOL: Use get_job_status tool with the returned job_id
            """

    @track_tool_execution()
    def run(
        self, *, custom_field_values: list[CatalogAssetMetadataPayloadItem]
    ) -> dict:
        return self.api.update_catalog_asset_metadata(custom_field_values)


class CheckJobStatusTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "check_job_status"

    @staticmethod
    def _get_description() -> str:
        return """
        Check the status of a bulk metadata job in Alation by job ID.

        Parameters:
        - job_id (required, integer): The integer job identifier returned by a previous bulk operation.

        Use this tool to:
        - Track the progress and result of a bulk metadata job (such as catalog asset metadata updates).

        Example:
            check_job_status(123)

        Response Behavior:
        Returns the job status and details as a JSON object.
        """

    @track_tool_execution()
    def run(self, *, job_id: int) -> dict:
        return self.api.check_job_status(job_id)


class GenerateDataProductTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

        # Cache the schema to avoid repeated requests, store as a tuple: (schema_content, timestamp)
        self._cached_schema: Optional[tuple[str, float]] = None

        # Cache lifetime in seconds (e.g., 1 hour)
        self.CACHE_TTL_SECONDS = 3600

    def clear_cache(self):
        """Manually clears the cached data product schema."""
        self._cached_schema = None
        logger.info("Data product schema cache has been cleared.")

    @staticmethod
    def _get_name() -> str:
        return "generate_data_product"

    @staticmethod
    def _get_description() -> str:
        return """
        Returns a complete set of instructions, including the current Alation Data Product schema and a valid example, for creating an Alation Data Product. Use this to prepare the AI for a data product creation task.

        This tool provides:
        - The current Alation Data Product schema specification (fetched dynamically from your instance)
        - A validated example following the schema
        - Detailed instructions for converting user input to valid YAML
        - Guidelines for handling required vs optional fields
        - Rules for avoiding hallucination of data not provided by the user

        Use this tool when you need to:
        - Convert semantic layers to Alation Data Products
        - Create data product specifications from user descriptions
        - Understand the current schema requirements
        - Get examples of properly formatted data products

        No parameters required - returns the complete instruction set with the latest schema from your Alation instance.
        """

    @track_tool_execution()
    def run(self) -> str:
        """
        Assembles and returns the complete instructional prompt for creating
        an Alation Data Product using the current schema from the instance.
        """
        schema_content = get_schema_content(self)
        example_content = get_example_content()
        prompt_instructions = get_prompt_instructions()

        final_instructions = prompt_instructions.format(
            schema=schema_content, example=example_content
        )
        return final_instructions


class CheckDataQualityTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_data_quality"

    @staticmethod
    def _get_description() -> str:
        return """
            Checks data quality for a list of tables or an individual SQL query.

            WHEN TO USE:
            - User directly asks to "check data quality"
            - User requests to "validate data quality" or "assess quality" of a sql query or table
            - User asks "is this data reliable/trustworthy?"
            - User says "run data quality check" or similar explicit request

            IMPORTANT: Either a table_ids or sql_query parameter is required. If sql_query is provided, either ds_id or db_uri must also be included.

            VALID PARAMETER COMBINATIONS:
            1. table_ids (for checking specific tables)
            2. sql_query + ds_id (recommended for SQL query validation)
            3. sql_query + db_uri (recommended for SQL query validation when ds_id is unknown)

            PARAMETERS:
            - table_ids: List of table identifiers (max 30) - use alation_context to get table ids first
            - sql_query: SQL query to analyze for quality issues
            - ds_id: A data source id from Alation
            - db_uri: A database URI as an alternative to ds_id. e.g. postgresql://@host:port/dbname
            - output_format: "json" (default) or "yaml_markdown" for more compact responses
            - dq_score_threshold: Quality threshold (0-100), tables below this are flagged. Defaults to 70.

            Returns a data quality summary and item level quality statements."""

    @track_tool_execution()
    def run(
        self,
        *,
        table_ids: Optional[list] = None,
        sql_query: Optional[str] = None,
        db_uri: Optional[str] = None,
        ds_id: Optional[int] = None,
        bypassed_dq_sources: Optional[list] = None,
        default_schema_name: Optional[str] = None,
        output_format: Optional[str] = None,
        dq_score_threshold: Optional[int] = None,
    ):
        try:
            return self.api.check_sql_query_tables(
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


class GetCustomFieldsDefinitionsTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_custom_fields_definitions"

    @staticmethod
    def _get_description() -> str:
        return """
        Retrieves all custom field definitions from the Alation instance.

        Custom fields are user-defined metadata fields that organizations create to capture 
        business-specific information beyond Alation's standard fields (title, description, stewards).

        Common examples of custom fields include:
        - Data Classification (e.g., "Public", "Internal", "Confidential", "Restricted")
        - Business Owner or Data Owner
        - Data Retention Period
        - Business Glossary Terms
        - Compliance Tags
        - Source System
        - Update Frequency
        - Business Purpose

        WHEN TO USE:
        - To understand what custom metadata fields are available in the instance
        - To validate custom field names and types before bulk updates
        - Before generating data dictionary files that need to include custom field updates

        IMPORTANT NOTES:
        - Admin permissions provide access to all custom fields created by the organization
        - Non-admin users will receive built-in fields only (title, description, steward) with appropriate messaging
        - Returns both user-created custom fields and some built-in fields
        - Use the 'allowed_otypes' field to understand which object types each field supports
        - Field types include: TEXT, RICH_TEXT, PICKER, MULTI_PICKER, OBJECT_SET, DATE, etc.
        - If users asks for updating custom fields, please do the below step by step
            1. Please format the objects to show the changes in a csv format with object id, name and changed custom field value.
            2. Once you showed the csv file, say the user can call generate_data_dictionary_instructions tool to create a data dictionary which could be uploaded to alation UI for bulk updates.

        Parameters:
        No parameters required - returns all custom field definitions for the instance.
        chat_id (optional): Chat session identifier.


        Returns:
        List of custom field objects with exactly these properties:
        - id: Unique identifier for the custom field
        - name_singular: Display name shown in the UI (singular form)
        - field_type: The type of field (RICH_TEXT, PICKER, MULTI_PICKER, OBJECT_SET, DATE, etc.)
        - allowed_otypes: List of object types that can be referenced by this field (e.g., ["user", "groupprofile"]). Only applicable to OBJECT_SET fields.
        - options: Available choices for picker-type fields (null for others)
        - tooltip_text: Optional description explaining the field's purpose (null if not provided)
        - allow_multiple: Whether the field accepts multiple values
        - name_plural: Display name shown in the UI (plural form, empty string if not applicable)
        
        Admin users: Returns all custom fields plus built-in fields
        Non-admin users: Returns only built-in fields (id: 3 (title), 4 (description), 8 (steward))
        """

    @track_tool_execution()
    def run(self, chat_id: Optional[str] = None) ->Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        """
        Retrieve all custom field definitions from the Alation instance.

        Returns:
            Dict containing either:
            - Success: {"custom_fields": [...], "usage_guide": {...}} with filtered field definitions and guidance
            - For non-admin users (403): Built-in fields only with appropriate messaging
            - Error: {"error": {...}} with error details
        """
        try:
            ref = self.api.get_custom_field_definitions_stream(chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}

    def _get_built_in_fields_response(self) -> Dict[str, Any]:
        """
        Return built-in field definitions for non-admin users using shared fields functions.

        Returns:
            Dict containing built-in fields and usage guidance for non-admin users
        """
        return {
            "custom_fields": get_built_in_fields_structured(),
            "message": "Admin permissions required for custom fields. Showing built-in fields only.",
            "usage_guide": get_built_in_usage_guide(),
        }


class GetDataDictionaryInstructionsTool:
    """
    Generates comprehensive instructions for creating Alation Data Dictionary CSV files.

    This tool provides LLMs with complete formatting rules, validation schemas, and examples
    for transforming object metadata into properly formatted data dictionary CSVs.
    """

    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_data_dictionary_instructions"

    @staticmethod
    def _get_description() -> str:
        return """
        Generates comprehensive instructions for creating Alation Data Dictionary CSV files.

        Automatically fetches current custom field definitions and provides:
        - Complete CSV format specifications with required headers
        - Custom field formatting rules and validation schemas
        - Object hierarchy grouping requirements
        - Field-specific validation rules and examples
        - Ready-to-use transformation instructions for LLMs

        WHEN TO USE:
        - Before generating data dictionary CSV files for bulk metadata upload
        - To understand proper formatting for different object types and custom fields
        - When transforming catalog objects and metadata into upload-ready format

        WORKFLOW:
        1. Call this tool to get comprehensive formatting instructions
        2. Use the instructions to transform your object data into properly formatted CSV
        3. Upload the CSV file to Alation using the Data Dictionary interface

        OBJECT HIERARCHY REQUIREMENTS:
        - RDBMS objects (data, schema, table, attribute) must be in ONE CSV file together
        - BI objects (bi_server, bi_folder, bi_datasource, bi_datasource_column, bi_report, bi_report_column) need separate CSV
        - Documentation objects (glossary_v3, glossary_term) need separate CSV
        - Title field is NOT supported for BI objects (read-only from source system)

        No parameters required - returns complete instruction set with latest schema.

        Returns:
        Complete instruction set with formatting rules, validation schemas, and examples
        """

    @track_tool_execution()
    def run(self) -> str:
        """
        Generate comprehensive data dictionary CSV formatting instructions.

        Automatically fetches current custom field definitions and provides complete
        formatting rules, validation schemas, and examples.

        Returns:
            str: Complete instruction set for creating data dictionary CSV files
        """
        try:
            # Always fetch fresh custom fields
            custom_fields = []
            try:
                custom_fields_response = self.api.get_custom_fields()
                custom_fields = filter_field_properties(custom_fields_response)
            except AlationAPIError as e:
                # Non-admin users will get 403 - provide instructions without custom fields
                if e.status_code == 403:
                    logger.info(
                        "Non-admin user detected, providing built-in fields only"
                    )
                    custom_fields = []
                else:
                    raise

            # Generate the comprehensive instructions
            instructions = build_optimized_instructions(custom_fields)
            return instructions

        except AlationAPIError as e:
            return {"error": e.to_dict()}


class SignatureCreationTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_signature_creation_instructions"

    @staticmethod
    def _get_description() -> str:
        return """Returns comprehensive instructions for creating the signature parameter for alation_context
        and bulk_retrieval tools.

        Provides object type guidance, field selection rules, filter application logic,
        and signature templates for use with alation_context and bulk_retrieval tools.

        USE THIS TOOL WHEN:
        - Need guidance on creating proper signatures
        - Want to understand available object types and fields
        - Building complex queries with filters
        - Learning signature format and structure

        PARAMETERS:
        chat_id (optional): Chat session identifier

        RETURNS:
        - Complete signature creation instructions
        - Templates and examples
        - Best practices and validation rules
        """

    @track_tool_execution()
    def run(self, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.get_signature_creation_instructions_stream(chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class AnalyzeCatalogQuestionTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "analyze_catalog_question"

    @staticmethod
    def _get_description() -> str:
        return """MANDATORY FIRST STEP - CALL THIS FIRST
        
        PRIMARY ENTRY POINT: Analyzes catalog questions and returns workflow guidance.

        Call this tool FIRST for all data catalog questions.

        Provides step-by-step guidance on how to analyze questions, gather metadata,
        create optimized signatures, and execute searches effectively.

        USE THIS TOOL WHEN:
        - Need guidance on how to handle complex Alation search questions
        - Want to understand the optimal workflow for data catalog queries
        - Building sophisticated search capabilities
        - Learning how to orchestrate multiple tools effectively

        RETURNS:
        - Complete 5-step workflow instructions
        - Decision trees for tool selection
        - Question analysis guidance
        - Best practices for search orchestration
        """

    @track_tool_execution()
    def run(self, *, question: str, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.analyze_catalog_question_stream(
                question=question,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class CatalogContextSearchAgentTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "catalog_context_search_agent"

    @staticmethod
    def _get_description() -> str:
        return """
        Catalog Context Search Agent for searching catalog objects with enhanced context.

        This agent provides contextual search capabilities across the Alation catalog,
        understanding relationships and providing enriched results.

        Parameters:
        - message (required, str): Natural language description of what you're searching for
        - chat_id (optional, str): Chat session identifier

        Returns:
        Contextually-aware search results with enhanced metadata and relationships.
        """

    @track_tool_execution()
    def run(self, *, message: str, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.catalog_context_search_agent_stream(
                message=message,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class QueryFlowAgentTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "query_flow_agent"

    @staticmethod
    def _get_description() -> str:
        return """
        Query Flow Agent for SQL query workflow management.

        This agent manages complex SQL query workflows, helping with query optimization,
        execution planning, and result analysis.

        Parameters:
        - message (required, str): Description of your query workflow needs
        - marketplace_id (required, str): The ID of the marketplace to work with
        - chat_id (optional, str): Chat session identifier

        Returns:
        Query workflow guidance, optimization suggestions, and execution plans.
        """

    @track_tool_execution()
    def run(self, *, message: str, marketplace_id: str, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.query_flow_agent_stream(
                message=message,
                marketplace_id=marketplace_id,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class SqlQueryAgentTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "sql_query_agent"

    @staticmethod
    def _get_description() -> str:
        return """
        SQL Query Agent for SQL query generation and analysis.

        This agent specializes in generating, analyzing, and optimizing SQL queries
        based on natural language descriptions of data needs.

        Parameters:
        - message (required, str): Description of the data you need or SQL task
        - data_product_id (required, str): The ID of the data product to work with
        - chat_id (optional, str): Chat session identifier

        Returns:
        SQL queries, query analysis, optimization suggestions, and execution guidance.
        """

    @track_tool_execution()
    def run(self, *, message: str, data_product_id: str, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.sql_query_agent_stream(
                message=message,
                data_product_id=data_product_id,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class GetDataSourcesTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_data_sources_tool"

    @staticmethod
    def _get_description() -> str:
        return """
        Retrieve available data sources from the catalog.

        This tool lists data sources that are available in the Alation catalog.

        Parameters:
        - limit (optional, int): Maximum number of data sources to return (default: 100)
        - chat_id (optional, str): Chat session identifier

        Returns:
        List of available data sources with their metadata and connection information.
        """

    @track_tool_execution()
    def run(self, *, limit: int = 100, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.get_data_sources_tool_stream(limit=limit, chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class CustomAgentTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "custom_agent"

    @staticmethod
    def _get_description() -> str:
        return """
        Execute a custom agent configuration by its UUID.

        This tool allows you to interact with custom agent configurations that have been
        created in the system. Each agent has its own input schema and specialized capabilities.

        Parameters:
        - agent_config_id (required, str): The UUID of the agent configuration to use
        - payload (required, Dict[str, Any]): The payload to send to the agent. Must conform
          to the agent's specific input JSON schema. Common patterns include:
          * {"message": "your question"} for most conversational agents
          * More complex schemas depending on the agent's configuration
        - chat_id (optional, str): Chat session identifier

        Returns:
        Agent response based on the specific agent's capabilities and output schema.

        Usage Examples:
        - custom_agent(agent_config_id="550e8400-e29b-41d4-a716-446655440000",
                      payload={"message": "Analyze this data"})
        - custom_agent(agent_config_id="custom-uuid",
                      payload={"query": "specific request", "context": {...}})

        Note: The payload structure depends on the input schema defined for each specific
        agent configuration. Consult the agent's documentation for required fields.
        """

    @track_tool_execution()
    def run(
        self,
        *,
        agent_config_id: str,
        payload: Dict[str, Any],
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.custom_agent_stream(
                agent_config_id=agent_config_id, payload=payload, chat_id=chat_id
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


def csv_str_to_tool_list(tool_env_var: Optional[str] = None) -> List[str]:
    if tool_env_var is None:
        return []
    uniq = set()
    if tool_env_var:
        for tool_str in tool_env_var.split(","):
            tool_str = tool_str.strip()
            uniq.add(tool_str)
    return list(uniq)
