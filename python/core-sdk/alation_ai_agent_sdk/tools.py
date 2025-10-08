import re
import logging

from typing import (
    Any,
    Dict,
    List,
    Optional,
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

    question (required): Exact user question, unmodified
    signature (optional): JSON specification of fields/filters

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
    def run(self, *, question: str, signature: Optional[Dict[str, Any]] = None):
        try:
            return self.api.get_context_from_catalog(question, signature)
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

    signature (required, JSON):
        For complete signature specification, field options, and filter rules,
        call get_signature_creation_instructions() first.

    ## USE CASES

    ✓ "List ALL tables in finance schema"
    ✓ "Get all endorsed tables from data source 5"
    ✓ "Show tables with PII classification"

    ✗ "Find sales-related tables" → use alation_context (concept discovery)
    ✗ "Tables about customers" → use alation_context (semantic search)

    See get_signature_creation_instructions() for complete usage guide.
    """

    @track_tool_execution()
    def run(self, *, signature: Optional[Dict[str, Any]] = None):
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
            return self.api.get_bulk_objects_from_catalog(signature)
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
            1. Pleast format the objects to show the changes in a csv format with object id, name and changed custom field value. 
            2. Once you showed the csv file, say the user can call generate_data_dictionary_instructions tool to create a data dictionary which could be uploaded to alation UI for bulk updates.

        No parameters required - returns all custom field definitions for the instance.

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
    def run(self) -> Dict[str, Any]:
        """
        Retrieve all custom field definitions from the Alation instance.

        Returns:
            Dict containing either:
            - Success: {"custom_fields": [...], "usage_guide": {...}} with filtered field definitions and guidance
            - For non-admin users (403): Built-in fields only with appropriate messaging
            - Error: {"error": {...}} with error details
        """
        try:
            raw_custom_fields = self.api.get_custom_fields()
            filtered_custom_fields = filter_field_properties(raw_custom_fields)

            return {
                "custom_fields": filtered_custom_fields,
                "usage_guide": {
                    "object_compatibility": "For Object Set fields, the 'allowed_otypes' array specifies what type of Alation objects can be selected as the value for this field. For example, a 'Business Owner' field would have ['user', 'groupprofile'] as its allowed otypes because only users or groups can be assigned as the value. This does not control which objects the field can be applied to.",
                    "value_validation": "For PICKER and MULTI_PICKER fields, the 'options' array contains all valid values that can be entered. For other field types, 'options' is null. The 'allow_multiple' field indicates whether a single value or multiple values can be provided. MULTI_PICKER fields always allow multiple values, OBJECT_SET fields vary based on 'allow_multiple', and TEXT/RICH_TEXT/PICKER/DATE fields are always single-value.",
                    "display_names": "Use 'name_singular' for field labels and column headers in user interfaces. Use 'name_plural' when displaying fields that have multiple values selected (when 'allow_multiple' is true). If 'name_plural' is empty, fall back to 'name_singular' or add 's' for pluralization.",
                    "field_types": "TEXT = single line text, RICH_TEXT = formatted text with HTML, PICKER = single selection dropdown, MULTI_PICKER = multiple selection checkboxes, OBJECT_SET = references to users/groups/objects, DATE = date picker. Use 'field_type' to determine appropriate input validation and UI controls.",
                    "csv_headers": "For data dictionary CSV files, use a combination of the field's ID and name for the column headers. The required format is id|field_name (e.g., 4|description or 10020|Business Owner). This is required for Alation to recognize which field to update.",
                },
            }
        except AlationAPIError as e:
            if e.status_code == 403:
                logger.info("Non-admin user detected, providing built-in fields only")
                return self._get_built_in_fields_response()
            else:
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

        RETURNS:
        - Complete signature creation instructions
        - Templates and examples
        - Best practices and validation rules
        """


    @track_tool_execution()
    def run(self):
        return """ALATION SIGNATURE CREATION GUIDE
    
    ## PRIMARY TASK
    Generate a valid JSON signature for alation_context and bulk_retrieval tools calls based on user questions.
    
    ## REQUIRED OUTPUT FORMAT
    Your response must be ONLY valid JSON in this structure:
    
    {
      "object_type": {
        "fields_required": ["field1", "field2", ...],
        "search_filters": {
          "domain_ids": [123],
          "fields": {
            "filter_name": [value1, value2]
          }
        },
        "child_objects": {
          "child_type": {
            "fields": ["field1", "field2"]
          }
        },
        "limit": 10
      }
    }
    
    Do NOT include explanations, markdown formatting, or text outside the JSON.
    
    ## MANDATORY VALIDATION BEFORE OUTPUT
    You MUST complete this validation and show your work:
    
    <validation_check>
    For each object type in your planned signature:
      <object type="[name]">
        Fields to include: [list]
        → Check: All fields exist in this object's Available Fields? [YES/NO]
    
        Filters to include: [list]
        → Check each filter:
          <filter name="[filter_name]">
            Is "[filter_name]" in this object's supported_filters? [YES/NO]
            Decision: [INCLUDE/REMOVE]
          </filter>
      </object>
    </validation_check>
    
    CRITICAL: Only include filters that pass validation (YES).
    
    
    ## STEP-BY-STEP PROCESS
    
    ### STEP 1: ANALYZE QUESTION FOR OBJECT TYPES
    
    Available Object Types: schema, table, column, query (SQL query), documentation, bi_report, bi_field, bi_folder
    
    Selection Rules:
    - User specified object type → Use only that type
      Example: "What are the sales tables in ABC domain" → table only
      Example: "Explain the sales forecast query" → query only
    
    - Cross-reference needed → Multiple types
      Example: "Policies about sales data" → table + documentation
    
    - Comprehensive information → Multiple types
      Example: "Everything about revenue" → table + query + bi_report + documentation
    
    - Ambiguous question → Multiple types
      Example: "Find customer information" → table + documentation + bi_report
    
    ### STEP 2: CHOOSE FIELDS FOR EACH OBJECT TYPE
    
    <available_fields>
    Object Type         | Required Fields                                                 | Optional Fields
    ────────────────────|─────────────────────────────────────────────────────────────────|────────────────────────────────────
    table               | name, title, description, url, object_id                        | columns, common_joins, common_filters, source_comment, custom_fields
    schema              | name, title, description, url, object_id                        | source_comment, custom_fields
    column              | name, title, data_type, url, object_id                          | description, sample_values, source_comment, custom_fields
    documentation       | title, content, url, object_id, custom_fields                   | -
    query               | title, description, content, url, object_id                     | mentioned_tables, custom_fields
    bi_report           | name, description, bi_object_type, url, object_id, bi_fields    | source_comment, custom_fields
    bi_field            | name, description, bi_object_type, url, object_id               | data_type, role, expression, source_comment, custom_fields
    bi_folder           | name, description, bi_object_type, url, object_id               | source_comment, custom_fields
    </available_fields>
    
    Field Selection Logic:
    
    ALWAYS INCLUDE: Required Fields for each object type
    
    OVERRIDE RULE - Explicit User Requests (HIGHEST PRIORITY):
    - "show me joins" / "how does it connect" / "relationships" → common_joins
    - "show me filters" / "how is it used" / "usage patterns" → common_filters
    - "show me columns" / "table structure" / "schema" → columns
    - "show me sample data" / "example values" / "what looks like" → sample_values
    - "what tables does this query use" → mentioned_tables
    - "how is [X] calculated" / "formula" / "calculation logic" → bi_fields (with expression)
    - "show me fields" / "what fields in report" → bi_fields
    
    DEFAULT FOR DETAILED INFORMATION REQUESTS (not bulk enumeration):
    When asking about specific named objects OR comprehensive understanding:
    - "Tell me about [object_name]"
    - "Explain [object_name]"
    - "What is [object_name]?"
    - "How does X work?"
    
    → Include for tables: columns, common_joins, common_filters
    → Include for columns: sample_values
    → Include for bi_reports: bi_fields
    
    DEFAULT FOR BULK ENUMERATION REQUESTS:
    When listing/finding/discovering many objects:
    - "List all tables"
    - "Show me sales tables"
    - "What tables contain..."
    
    → Do NOT include: common_joins, common_filters, sample_values
    → Include only: Required Fields
    
    IMPORTANT: FIELDS ≠ FILTERS
    - FIELDS → "fields_required"
    - FILTERS → "search_filters"
    
    ### STEP 2.1: CHOOSE CHILD OBJECTS (IF NEEDED)
    
    <supported_child_objects>
    {
      "Table": {
        "supported_child_objects": {
          "columns": {
            "otype": "column",
            "allowed_fields": ["name", "title", "description", "data_type", "url", "sample_values", "object_id", "object_type", "source_comment"]
          }
        }
      },
      "Query": {
        "supported_child_objects": {
          "mentioned_tables": {
            "otype": "table",
            "allowed_fields": ["name", "title", "description", "url", "common_joins", "common_filters", "columns", "object_id", "object_type"]
          }
        }
      },
      "BI Report": {
        "supported_child_objects": {
          "bi_fields": {
            "otype": "bi_report_column",
            "allowed_fields": ["name", "data_type", "role", "description", "expression"]
          }
        }
      }
    }
    </supported_child_objects>
    
    Rule: If you include an optional field that represents a child object (columns, mentioned_tables, bi_fields), you MUST define a child_objects block.
    
    Example:
    {
      "table": {
        "fields_required": ["name", "title", "description", "url", "columns"],
        "child_objects": {
          "columns": {
            "fields": ["name", "data_type", "description"]
          }
        }
      }
    }
    
    For bi_reports with bi_fields, ALWAYS include: name, description, expression, role, data_type.
    
    ### STEP 2.2: HANDLE CUSTOM FIELDS

    If the question mentions attributes NOT in predefined lists → Assume custom field
    
    Example custom field indicators:
    - "PII Classification"
    - "Data Classification"
    - "Department"
    - "Priority Level"
    
    Workflow:
    1. Identify potential custom field in question
    2. Use custom field definitions provided by get_custom_fields_definitions()
    3. Add "custom_fields" to fields_required
    4. Add field IDs to custom_fields list
    5. To filter: use cf[field_id] format in search_filters
    
    Example:
    Question: "Fetch all tables that are PII"
    
    Signature:
    {
      "table": {
        "fields_required": ["name", "title", "description", "url", "custom_fields"],
        "custom_fields": [25],
        "search_filters": {
          "fields": {
            "cf[25]": ["PII", "Verified PII", "Sensitive PII"]
          }
        },
        "limit": 50
      }
    }
    
    ### STEP 3: APPLY FILTERS WITH VALIDATION
    
    <supported_filters_by_object_type>
    {
      "Schema": {
        "supported_filters": ["ds", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "Table": {
        "supported_filters": ["ds", "schema_name", "table_type", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value", "schema"]
      },
      "Column (Attribute)": {
        "supported_filters": ["ds", "schema_name", "schema", "data_type", "table", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "BI Folder": {
        "supported_filters": ["bi_server_id", "parent_folder", "bi_owner", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "BI Report": {
        "supported_filters": ["bi_server_id", "parent_folder", "bi_owner", "is_dashboard", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "BI Field": {
        "supported_filters": ["bi_server_id", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "Query": {
        "supported_filters": ["ds", "author", "published", "scheduled", "tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value"]
      },
      "Documentation": {
        "supported_filters": ["tag_ids", "flag_types", "domain_ids", "policy_ids", "custom_field_value", "folder"]
      }
    }
    </supported_filters_by_object_type>
    
    <filter_usage_guide>
    {
      "filter_instructions": {
        "general_notes": [
          "Filters go in 'search_filters' section",
          "All filter values must be lists, even for single values"
        ],
        "filters": {
          "author": {"description": "Filter by query author ID", "type": "list[int]", "example": "\"author\": [123]"},
          "bi_owner": {"description": "Filter by BI object owner", "type": "list[str]", "example": "\"bi_owner\": [\"John Doe\"]"},
          "bi_server_id": {"description": "Filter by BI server ID. RDBMS DS ID and BI server ID are different", "type": "list[int]", "example": "\"bi_server_id\": [123]"},
          "cf[field_id]": {"description": "Filter by custom field value", "type": "list[str or int]", "example": "\"cf[12345]\": [\"value1\"]"},
          "data_type": {"description": "Filter by attribute data type", "type": "list[str]", "example": "\"data_type\": [\"varchar\"]"},
          "domain_ids": {"description": "Filter by domain ID", "type": "list[int]", "example": "\"domain_ids\": [42, 123]"},
          "ds": {"description": "Filter by data source ID", "type": "list[int]", "example": "\"ds\": [1, 5]"},
          "flag_types": {"description": "Filter by trust flags", "type": "list[str]", "accepted_values": ["Endorsement", "Deprecation", "Warning"], "example": "\"flag_types\": [\"Endorsement\"]"},
          "folder": {"description": "Filter by folder ID for documentation", "type": "list[int]", "example": "\"folder\": [123]"},
          "is_dashboard": {"description": "Filter BI reports that are dashboards", "type": "list[bool]", "example": "\"is_dashboard\": [true]"},
          "parent_folder": {"description": "Filter by parent folder of BI object", "type": "list[str]", "example": "\"parent_folder\": [\"Sales Reports\"]"},
          "policy_ids": {"description": "Filter by policy ID", "type": "list[int]", "example": "\"policy_ids\": [10, 20]"},
          "published": {"description": "Filter by published status", "type": "list[bool]", "example": "\"published\": [true]"},
          "scheduled": {"description": "Filter queries that are scheduled", "type": "list[bool]", "example": "\"scheduled\": [true]"},
          "schema": {"description": "Filter by schema ID", "type": "list[int]", "example": "\"schema\": [123]"},
          "schema_name": {"description": "Filter by schema name", "type": "list[str]", "example": "\"schema_name\": [\"finance\"]"},
          "table": {"description": "Filter by table ID", "type": "list[int]", "example": "\"table\": [123]"},
          "table_type": {"description": "Filter by table type", "type": "list[str]", "accepted_values": ["VIEW", "TABLE"], "example": "\"table_type\": [\"VIEW\"]"},
          "tag_ids": {"description": "Filter by tag ID", "type": "list[int]", "example": "\"tag_ids\": [1, 20]"}
        }
      }
    }
    </filter_usage_guide>
    
    ### STEP 3.0: IDENTIFY FILTERING INTENT (MANDATORY)
    
    Before selecting filters, systematically extract constraints from the question:
    
    <filter_intent_analysis>
    1. Identify constraint phrases:
       Scan for: "in [X]", "from [X]", "within [X]", "of [X]", "at [X]", "by [X]"
       Found phrases: [list them]
    
    2. For each phrase, determine constraint type:
       - Is it a container name? (specific named location)
       - Is it a category? (type, status, classification)
       - Is it an identifier? (ID, name with specific format)
       
    3. Match constraint to filter category:
       - Hierarchical location: folder, schema, workbook, parent_folder
       - System identifier: ds, bi_server_id, domain_ids
       - Metadata attribute: table_type, published, scheduled
       - Owner/Author: bi_owner, author
       - Custom attribute: cf[field_id]
    
    4. For each object type in your signature:
       Look up its supported_filters list
       Check which filters match your identified constraints
       
    Final filter mapping:
    - [object_type]: [filter_name] with value [X]
    </filter_intent_analysis>
    
    ### STEP 3.1: VALIDATE AGAINST SCHEMA

    CRITICAL VALIDATION RULE:
    Before adding ANY filter to search_filters:
    1. Look up object type in supported_filters_by_object_type
    2. Check if filter exists in that object's supported_filters list
    3. If NOT in list → DO NOT INCLUDE that filter. ex: We have schema_name but there is no "name" or "table_name" or "ds_name" filter for any object type.
    4. If in list → Include in correct location (domain_ids vs fields)
    5. Data source IDs are for RDBMS objects (tables/queries). BI server IDs are separate and not provided in context. Only use if user has provided it.
    
    
    Example validation:
    Question: "Show me sales tables and dashboards from the Analytics data source (id=10)"
    
    For TABLE:
      Check: Is "ds" in Table's supported_filters?
      Answer: YES → Include "ds": [10]
    
    For BI_REPORT:
      Check: Is "ds" in BI Report's supported_filters?
      Answer: NO → Do NOT include "ds"
      Check: Is "bi_server_id" in BI Report's supported_filters?
      Answer: YES → Include "bi_server_id": [10]
    
    
    ### STEP 4: CONSTRUCT FINAL JSON SIGNATURE
    
    Structure Rules:
    - Top level: object types as keys
    - Each object has: fields_required, search_filters (optional), child_objects (optional), limit (optional)
    - search_filters structure:
      - domain_ids → direct child of search_filters
      - All other filters → nested under "fields" key
    
    Validation Table Format:
    | Object Type | Filter | Supported? | Action |
    |-------------|--------|-----------|--------|
    | table       | ds     | ✓ YES     | INCLUDE |
    | bi_report   | ds     | ✗ NO      | REMOVE  |
    | bi_report   | bi_server_id | ✓ YES | INCLUDE |
    
    Example Structure:
    {
      "table": {
        "fields_required": ["name", "title", "description", "url", "object_id", "columns"],
        "search_filters": {
          "domain_ids": [42],
          "fields": {
            "tag_ids": [101]
          }
        },
        "child_objects": {
          "columns": {
            "fields": ["name", "data_type", "description"]
          }
        },
        "limit": 10
      }
    }
    
    ## SELF-CHECK BEFORE FINALIZING
    
    <self_validation>
    □ Did I complete the <validation_check> for ALL filters?
    □ Did I remove ALL filters not in supported_filters list?
    □ Are domain_ids and other filters in correct locations?
    □ Did I include ALL required fields for each object type?
    □ Did I define child_objects for columns/mentioned_tables/bi_fields?
    □ Is my JSON valid with proper syntax?
    □ Did I include ONLY JSON with no explanations or markdown?
    </self_validation>
    
    If ANY box is unchecked → REVISE before outputting.
    
    ## COMPLETE EXAMPLE
    
    User Question: "Show me the top 5 sales tables in the marketing domain, including their columns and any related queries."
    
    <validation_check>
      <object type="table">
        Fields: name, title, description, url, object_id, columns
        → Check: All in table's Available Fields? YES
    
        Filters: domain_ids
        → <filter name="domain_ids">
            In table's supported_filters? YES
            Decision: INCLUDE
          </filter>
      </object>
    
      <object type="query">
        Fields: title, description, content, url, object_id
        → Check: All in query's Available Fields? YES
    
        Filters: none
      </object>
    </validation_check>
    
    <self_validation>
    ☑ Validation complete for all filters
    ☑ All required fields included
    ☑ Child objects defined for columns
    ☑ JSON is valid
    ☑ Output is JSON only
    </self_validation>
    
    Expected Output:
    {
      "table": {
        "fields_required": [
          "name",
          "title",
          "description",
          "url",
          "object_id",
          "columns"
        ],
        "search_filters": {
          "domain_ids": [123]
        },
        "child_objects": {
          "columns": {
            "fields": [
              "name",
              "title",
              "data_type",
              "description"
            ]
          }
        },
        "limit": 5
      },
      "query": {
        "fields_required": [
          "title",
          "description",
          "content",
          "url",
          "object_id"
        ],
        "search_filters": {},
        "limit": 5
      }
    }"""


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
    def run(self, *, question: str):
        return f"""CATALOG QUESTION ANALYSIS WORKFLOW
    
    ## PRIMARY TASK
    Analyze this question and orchestrate the optimal search strategy:
    
    **Question:** "{question}"
    
    ## REQUIRED OUTPUT: ORCHESTRATION DECISION
    You must produce a clear decision on:
    1. Is the question actionable?
    2. Which object types to search for?
    3. Whether to use BULK or SEMANTIC search
    4. Which tools to call and in what order
    
    ## MANDATORY ANALYSIS BEFORE ORCHESTRATION
    
    <orchestration_analysis>
      <actionability_check>
        Is question actionable? [YES/NO]
        Reason: [one sentence]
        → If NO: Stop and provide clarification message
        → If YES: Continue to object detection
      </actionability_check>
    
      <object_detection>
        Keywords found in question: [list]
        Object types detected: [list]
        Reasoning: [how you mapped keywords to object types]
      </object_detection>
    
      <custom_fields_check>
        Does question mention governance/classification/custom concepts? [YES/NO]
        Should call get_custom_fields_definitions()? [YES/NO]
        Reasoning: [one sentence]
      </custom_fields_check>
    
      <routing_decision>
        Pattern detected: [BULK ENUMERATION / CONCEPT DISCOVERY]
        Has semantic concepts to discover? [YES/NO]
        Wants everything in a location? [YES/NO]
        → Decision: [bulk_retrieval / alation_context]
        Reasoning: [one sentence]
      </routing_decision>
    </orchestration_analysis>
    
    ## STEP-BY-STEP WORKFLOW
    
    ### STEP 1: ACTIONABILITY CHECK
    
    ❌ STOP & CLARIFY IF:
    - Catalog-wide requests without constraints:
      - "What tables are in catalog" / "Show all tables" / "List tables"
      - "Get all [objects]" (without data source/schema/domain specified)
      - Enumeration requests spanning entire catalog
    - Off-topic: non-catalog questions (weather, news, etc.)
    - Vague: "need data for project" (no specifics)
    
    ✅ PROCEED IF:
    - Specific data objects mentioned
    - Clear business context provided
    - Catalog-related request
    
    ### STEP 2: GATHER METADATA (Always Required)
    
    A. ALWAYS call: get_signature_creation_instructions()
       → Provides object types, fields, and standard filters
    
    B. CONDITIONALLY call: get_custom_fields_definitions()
    
       CALL IF question mentions:
       - "custom field", "custom metadata"
       - "governance", "classification"
       - "PII", "department", "priority", "business owner"
       - Any filtering by attributes NOT in standard filters
    
       DO NOT CALL IF question only uses:
       - Standard filters: data source, schema, domain, table names
       - Built-in object properties
    
    ### STEP 3: DETECT OBJECT TYPES (Before Analysis)
    
    <object_type_mapping>
    Keyword in Question       → Object Type    → Context Check
    ────────────────────────────────────────────────────────────
    "query"/"queries" (noun)  → query          → "explain X query", "find queries"
    "query" (verb)            → -              → "how to query data" (skip)
    "table"/"tables"          → table          → Always include
    "view"/"views"            → table          → Tables include views (filter by table_type to "VIEW")
    "column"/"columns"        → column         → Always include
    "attribute"/"field"       → column         → Always include
    "schema"/"schemas"        → schema         → Always include
    "database"/"datasource"   → schema         → Always include
    "report"/"dashboard"      → bi_report      → Always include
    "workbook"/"folder"       → bi_folder      → For BI contexts
    "documentation"/"article" → documentation  → Always include
    "guide"/"glossary"        → documentation  → Always include
    </object_type_mapping>
    
    CRITICAL: Detect object types BEFORE reformulating the question.
    
    ### STEP 4: ROUTE TO SEARCH METHOD
    
    #### CRITICAL LIMITATION: BULK RETRIEVAL CANNOT SEARCH BY NAME
    bulk_retrieval only supports filtering by:
    - Data source ID (ds)
    - Schema name (schema_name) or ID (schema)
    - Table type (table_type)
    - Flags, tags, domains, policies, custom fields
    - Other metadata attributes
    
    bulk_retrieval does NOT support:
    - Searching by object name
    - Pattern matching on names
    - Fuzzy name lookups
    - "Find table named X"
    
    → ANY question requiring name-based discovery MUST use alation_context (SEMANTIC SEARCH)

    IMPORTANT: Apply these checks IN ORDER (Priority 1 → Priority 2 → Priority 3)
    
    #### PRIORITY 1: CUSTOM FIELD ENUMERATION
    If custom_fields_definitions() was called AND question matches:
    - "Show [objects] that contain [custom_field_value]"
    - "Get [objects] with [custom_field_value]"
    - "Find [objects] classified as [value]"
    - "List [objects] that are [custom_value]"
    - "[objects] with [attribute] = [value]"
    
    
    → USE BULK RETRIEVAL
    Why: These are exact enumeration with custom field filters, not concept discovery
    
    #### PRIORITY 2: STRUCTURAL ENUMERATION
    If question matches:
    - "List ALL [objects] in [location]"
    - "Show ALL [objects] in [container]"
    - "What [objects] are in [place]"
    - "Get [objects] from [specific location]"
    
    → USE BULK RETRIEVAL
    Why: Wants complete list from known location
    
    #### PRIORITY 3: CONCEPT DISCOVERY
    If question matches:
    - "Find [CONCEPT] in [optional location]"
    - "[business domain term] data"
    - "Tables about [topic]"
    - Documentation/explanation queries
    - Fuzzy/exploratory search
    
    Examples:
    - "Find SALES tables" → SEMANTIC (discover "sales")
    - "Customer analysis data" → SEMANTIC (discover concept)
    
    → USE SEMANTIC SEARCH
    Why: Needs to discover what matches the concept
    
    Examples:
    | Question | Priority | Method | Why |
    |----------|----------|--------|-----|
    | "Show BI reports that contain PII" | P1 | BULK | Custom field enumeration |
    | "Tables classified as Confidential" | P1 | BULK | Custom field enumeration |
    | "List ALL tables in finance schema" | P2 | BULK | Structural enumeration |
    | "Find SALES tables in finance" | P3 | SEMANTIC | Concept discovery |
    
    ### STEP 5: EXECUTE SEARCH (Maximum 2 Calls)
    
    EXECUTION RULES:
    1. Make first search call with optimal signature
    2. Evaluate results:
       <result_evaluation>
         Results sufficient to answer? [YES/NO]
         If YES → Stop and generate answer
         If NO → Make ONE refined search
       </result_evaluation>
    3. NEVER exceed 2 search calls total
    4. If 2 searches fail → Explain what was tried and suggest refinement
    
    PATH A - BULK RETRIEVAL:
    
    1. Build structural signature with filters
    2. Call: bulk_retrieval(signature)
    3. Evaluate results
    4. If insufficient: Try semantic approach OR ask for clarification
    
    
    PATH B - SEMANTIC SEARCH:
    
    1. Build semantic signature with filters + concept fields
    2. Call: alation_context(question, signature)
    3. Evaluate results
    4. If insufficient: Try more specific filters OR ask for clarification
    
    ## STEP 6: CONSTRUCT RESPONSE WITH EXPLANATIONS
    
    ### WHEN TO EXPLAIN THE PROCESS:
    
    Include process explanations when:
    ✓ Multiple filters were applied (domain, custom fields, schema, etc.)
    ✓ Custom field filtering was used
    ✓ Complex queries with multiple object types
    ✓ User might benefit from understanding the search scope
    ✓ Results are filtered/limited in non-obvious ways
    
    Skip process explanations when:
    ✗ Simple, single-filter queries ("tables in schema X")
    ✗ Self-evident searches (user asked for exactly what was returned)
    ✗ Follow-up questions in same context
    
    ### HOW TO EXPLAIN THE PROCESS:
    
    Format: Brief, natural language summary BEFORE presenting results
    
    Template Structure:
    "I searched for [object types] [with these criteria]:
    - [Filter 1]: [value/explanation]
    - [Filter 2]: [value/explanation]
    [Additional context if relevant]
    
    Here's what I found:"
    
    Examples:
    
    Example 1 - Custom Field Filter:
    "I searched for tables in the Marketing domain (ID: 42) that are classified 
    as 'PII' in the Data Classification custom field. Here's what I found:"
    
    Example 2 - Multiple Filters:
    "I searched for published queries from the Sales data source (ID: 5) that 
    are endorsed. Here's what I found:"
    
    Example 3 - Semantic Search:
    "I searched for tables related to 'customer revenue' across the Finance 
    domain, looking at table names, descriptions, and documentation. Here's 
    what I found:"
    
    ## STEP 7: EXPLAIN RESULT COUNTS AND LIMITS
    
    ### WHEN TO EXPLAIN COUNTS/LIMITS:
    
    ALWAYS explain for:
    ✓ List/enumeration queries ("list all", "show all", "what are the")
    ✓ When limit was reached (returned count = signature limit)
    ✓ Bulk retrieval operations
    ✓ When results are clearly truncated
    
    SKIP count explanations for:
    ✗ Single object queries ("tell me about X table")
    ✗ Specific named object lookups
    ✗ When returned results are less than signature limit (obviously complete)
    ✗ Documentation/explanation queries
    
    ### HOW TO EXPLAIN COUNTS:
    
    <count_explanation_logic>
    IF returned_count < limit:
        → Optional: "Found [N] [objects]"
        → No need to mention more might exist
    
    IF returned_count == limit:
        → Required: "Found [N] [objects] (showing first [limit]). There may be 
           additional [objects] matching your criteria."

    </count_explanation_logic>
    
    Placement: Add count explanation AFTER process explanation, BEFORE results
    
    Examples:
    
    Example 1 - Limit Reached:
    "I searched for tables in the Finance schema classified as 'Confidential'.
    
    Found 20 tables (showing first 20). There may be additional tables matching 
    your criteria. Let me know if you'd like to see more results.
    
    Here are the tables:"
    
    Example 2 - Limit Not Reached:
    "I searched for endorsed BI reports in the Sales dashboard folder.
    
    Found 7 reports:
    [results...]"
    
    ## COMBINED EXAMPLE WITH BOTH EXPLANATIONS
    
    Question: "List all PII tables in the Marketing domain"
    
    Response:
    "I searched for tables in the Marketing domain (ID: 42) that are classified 
    as 'PII' or 'Sensitive PII' in the Data Classification custom field.
    
    Found 20 tables (showing first 20). There may be additional PII tables in 
    this domain. Let me know if you'd like to see more results.
    
    Here are the tables:
    
    1. **customer_email_list**
       - Description: Contains customer contact information including emails
       - URL: [link]
       - Classification: Sensitive PII
    
    2. **user_profiles**
       - Description: User account data with personal information
       - URL: [link]
       - Classification: PII

    ## SELF-CHECK BEFORE EXECUTING
    
    <self_validation>
    □ Did I complete <orchestration_analysis> for this question?
    □ Did I detect object types BEFORE analysis?
    □ Did I determine if custom fields are needed?
    □ Did I choose between BULK vs SEMANTIC with clear reasoning?
    □ Do I have a plan that limits searches to maximum 2 calls?
    □ If question is not actionable, did I prepare a clarification message?
    □ Did I plan to explain the process for complex/filtered queries?
    □ Did I plan to explain result counts for enumeration queries?
    □ If limit == returned_count, did I plan to mention potential truncation?
    </self_validation>
    
    If ANY box is unchecked → REVISE before proceeding.
    
    ## CLARIFICATION TEMPLATES
    
    TOO BROAD:
    "There are many [objects] in the catalog. Please specify which data source or schema you're interested in, and which specific [objects] you need."
    
    OFF-TOPIC:
    "I help find data assets in your Alation catalog. What data are you looking for?"
    
    VAGUE:
    "Please provide more context. For example: 'Find customer transaction tables in the finance schema for churn analysis'"
    
    ## COMPLETE EXAMPLE WITH EXPLANATIONS
    
    Question: "List all sales tables in the marketing domain"
    
    <orchestration_analysis>
      <actionability_check>
        Is question actionable? YES
        Reason: Specific object type (tables), domain (marketing), and concept (sales)
        → Continue to object detection
      </actionability_check>
    
      <object_detection>
        Keywords found: "tables", "marketing domain", "sales"
        Object types detected: table
        Reasoning: "tables" maps directly to table object type
      </object_detection>
    
      <custom_fields_check>
        Does question mention governance/classification? NO
        Should call get_custom_fields_definitions()? NO
        Reasoning: Uses standard filters (domain_ids) only
      </custom_fields_check>
    
      <routing_decision>
        Pattern detected: CONCEPT DISCOVERY + ENUMERATION
        Has semantic concepts? YES ("sales")
        Wants everything in location? YES ("list all")
        → Decision: alation_context (semantic needed for "sales" concept)
        Reasoning: Need to discover which tables match "sales" concept within domain
      </routing_decision>
      
      <explanation_planning>
        Should explain process? YES
        Reason: Domain filter applied + semantic search for "sales"
        
        Should explain counts? YES
        Reason: Enumeration query ("list all")
        
        Check for truncation? YES
        Reason: If limit reached, mention more may exist
      </explanation_planning>
    </orchestration_analysis>
    
    <self_validation>
    ☑ Orchestration analysis complete
    ☑ Object types detected (table)
    ☑ Custom fields check done (not needed)
    ☑ Routing decision made (SEMANTIC)
    ☑ Plan limits to 2 searches
    ☑ Question is actionable
    ☑ Process explanation planned
    ☑ Count explanation planned
    ☑ Truncation check planned
    </self_validation>
    
    EXECUTION PLAN:
    1. Call: get_signature_creation_instructions()
    2. Build signature for table object with domain filter, limit=20
    3. Call: alation_context("sales tables", signature_with_marketing_domain)
    4. Check: returned_count vs limit
    5. Construct response with explanations
    
    EXAMPLE RESPONSE:
    
    "I searched for tables related to 'sales' in the Marketing domain (ID: 42), 
    examining table names, descriptions, and associated documentation.
    
    Found 20 tables (showing first 20). There may be additional sales-related 
    tables in this domain. Let me know if you'd like to see more results.
    
    Here are the sales tables:
    
    1. **sales_transactions**
       - Description: Daily sales transaction records
       - URL: [link]
       - Columns: transaction_id, customer_id, amount, date
    
    2. **sales_forecasts**
       - Description: Monthly sales forecast data
       - URL: [link]
       - Columns: period, product_id, forecast_amount
    
    [...]"
    
    ## CRITICAL REMINDERS
    
    - ALWAYS complete <orchestration_analysis> before acting
    - ALWAYS detect object types from ORIGINAL question
    - Maximum 2 search calls per questionß
    - Stop after first search if results are sufficient
    - Use BULK for enumeration, SEMANTIC for concept discovery
    """

def csv_str_to_tool_list(tool_env_var: Optional[str] = None) -> List[str]:
    if tool_env_var is None:
        return []
    uniq = set()
    if tool_env_var:
        for tool_str in tool_env_var.split(","):
            tool_str = tool_str.strip()
            uniq.add(tool_str)
    return list(uniq)
