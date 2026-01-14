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
        logger.warning(
            "The AlationContextTool is deprecated and will be removed in a future release. Migrate your code and prompts to use CatalogContextSearchAgentTool instead."
        )
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
        return """LOW-LEVEL TOOL: Direct bulk enumeration of catalog objects with filters.

`catalog_context_search_agent` handles most catalog questions automatically.
Use `bulk_retrieval` when you need direct access to bulk catalog objects.

You MUST call `analyze_catalog_question` first to determine workflow.

WHEN TO USE:
- User explicitly requests "bulk_retrieval" or this specific tool
- Following instructions from `analyze_catalog_question`

WHAT THIS TOOL DOES:
Fetches complete sets of catalog objects without semantic search.
Use for structural enumeration, not concept discovery.

Supported: table, column, schema, query
Not supported: documentation objects

USE CASES:
✓ "List ALL tables in finance schema"
✓ "Get all endorsed tables from data source 5"
✓ "Show tables with PII classification"

✗ "Find sales-related tables" → use `get_context_by_id` (concept discovery)
✗ "Tables about customers" → use `get_context_by_id` (semantic search)

PARAMETERS:
- signature (required, JSON):
    For complete signature specification, field options, and filter rules,
    call `get_signature_creation_instructions` first.
- chat_id (optional): Chat session identifier
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


class GetContextByIdTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "get_context_by_id"

    @staticmethod
    def _get_description() -> str:
        return """LOW-LEVEL TOOL: Semantic search of Alation's data catalog using signature with search phrases.

`catalog_context_search_agent` handles most catalog questions automatically.
Use `get_context_by_id` when you need direct access to catalog context with custom signatures.

You MUST call `analyze_catalog_question` first to determine workflow.

WHEN TO USE:
- User explicitly requests "get_context_by_id" or this specific tool
- Following instructions from `analyze_catalog_question`
- You have a pre-built signature with search phrases

WHAT THIS TOOL DOES:
Fetches context from the catalog using search phrases embedded in the signature.
Returns structured data about tables, columns, documentation, queries, and BI objects.
Use for semantic search and concept discovery.

Supported: table, column, schema, query, documentation, BI objects

USE CASES:
✓ "Find sales-related tables" (concept discovery)
✓ "Tables about customer data" (semantic search)
✓ "Documentation on data warehouse" (content search)

✗ "List ALL tables in schema" → use `bulk_retrieval` (enumeration)
✗ "Get all endorsed tables" → use `bulk_retrieval` (filter-based list)

PARAMETERS:
- signature (required, JSON):
    For complete signature specification, field options, and filter rules,
    call `get_signature_creation_instructions` first.
- chat_id (optional): Chat session identifier
"""

    @track_tool_execution()
    def run(
        self,
        *,
        signature: Dict[str, Any],
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        if not signature:
            return {
                "error": {
                    "message": "Signature parameter is required",
                    "reason": "Missing Required Parameter",
                    "resolution_hint": "Provide a signature with search_phrases. Call get_signature_creation_instructions for format details.",
                }
            }
        try:
            ref = self.api.get_context_by_id_stream(signature=signature, chat_id=chat_id)
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
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.alation_lineage_stream(
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
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


class GenerateDataProductTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()

    @staticmethod
    def _get_name() -> str:
        return "generate_data_product"

    @staticmethod
    def _get_description() -> str:
        return """Returns comprehensive instructions for creating Alation Data Products.

        Provides the current Alation Data Product schema specification, a validated example,
        and detailed instructions for converting user input to valid YAML with strict rules
        for handling required vs optional fields and avoiding hallucination.

        WHEN TO USE:
        - Before creating a new Alation Data Product from user descriptions
        - To understand the current data product schema requirements
        - When converting semantic layers or metadata to Alation Data Products
        - To get examples of properly formatted data product YAML

        WORKFLOW:
        1. Call this tool to get comprehensive formatting instructions and schema
        2. Use the instructions to transform your data into properly formatted YAML
        3. Create the data product using the resulting YAML specification

        KEY FEATURES:
        - Fetches current schema dynamically from your Alation instance
        - Provides validated example following the schema
        - Guidelines for handling required vs optional fields

        Parameters:
        - chat_id (optional): Chat session identifier

        Returns:
        Complete instruction set with the latest schema from your Alation instance.
        """

    @track_tool_execution()
    def run(self, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        """
        Assembles and returns the complete instructional prompt for creating
        an Alation Data Product using the current schema from the instance.

        Parameters:
            chat_id (optional): Chat session identifier

        Returns:
            Complete instruction set for creating Alation Data Products
        """
        try:
            ref = self.api.generate_data_product_stream(chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
        except AlationAPIError as e:
            return {"error": e.to_dict()}


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
        return """Checks data quality for a list of tables or an individual SQL query.

    WHEN TO USE:
    - User directly asks to "check data quality"
    - User requests to "validate data quality" or "assess quality" of a SQL query or table
    - User asks "is this data reliable/trustworthy?"
    - User says "run data quality check" or similar explicit request

    IMPORTANT: Either table_ids OR sql_query parameter is required.
    If sql_query is provided, either ds_id or db_uri must also be included.

    VALID PARAMETER COMBINATIONS:
    1. table_ids (for checking specific tables)
    2. sql_query + ds_id (recommended for SQL query validation)
    3. sql_query + db_uri (recommended for SQL query validation when ds_id is unknown)

    REQUIRED PARAMETERS:
    - table_ids: List of table IDs to check (max 30). Use alation_context to get table IDs first.
      Example: [123, 456, 789]
    - OR sql_query: SQL query text to analyze for quality issues.
      Example: "SELECT * FROM schema.table WHERE date > '2024-01-01'"
    - If using sql_query, also provide:
      - ds_id: Data source ID from Alation (preferred)
        Example: 5
      - OR db_uri: Database URI as alternative to ds_id
        Example: "postgresql://@hostname:5432/dbname"

    OPTIONAL PARAMETERS:
    - output_format: Response format, either "json" (default) or "yaml_markdown" for compact output
      Default: "json" (returns structured JSON)
      Use "yaml_markdown" for more readable format when dealing with many tables
    - dq_score_threshold: Quality threshold (0-100), tables below this are flagged
      Default: 70
      Lower values are more lenient, higher values are stricter
    - bypassed_dq_sources: List of data quality source names to skip during checks
      Example: ["trust_flags", "native_dq"]
    - default_schema_name: Default schema name for unqualified table names in SQL query
      Example: "public"

    RESPONSE FORMAT:
    The response contains a "result" object with quality status and detailed findings:
    {
      "result": {
        "LOW DATA QUALITY": "warning message...",
        # or "HIGH DATA QUALITY" or "UNKNOWN DATA QUALITY"
        "Tables failing data quality checks": [
          "Table {name} has issue 1",
          "Table {name} has issue 2"
        ],
        "Inconclusive data quality checks": [
          "Table {name} has no data quality score"
        ]
      }
    }

    UNDERSTANDING THE RESPONSE:
    - Overall status: "LOW DATA QUALITY", "HIGH DATA QUALITY", or "UNKNOWN DATA QUALITY"
    - Tables failing: List of quality issues found (trust flags, DQ scores, deprecation warnings)
    - Inconclusive: Tables where quality could not be determined
    - "One bad apple" principle: If ANY table has quality issues, overall status is LOW

    COMMON EXAMPLES:
    - Check specific tables:
      get_data_quality(table_ids=[123, 456])

    - Check SQL query quality:
      get_data_quality(sql_query="SELECT * FROM orders", ds_id=5)

    - Check with custom threshold:
      get_data_quality(table_ids=[123], dq_score_threshold=80)

    - Get compact YAML output:
      get_data_quality(table_ids=[123, 456, 789], output_format="yaml_markdown")"""

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
        chat_id: Optional[str] = None,
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        try:
            ref = self.api.get_data_quality_tool_stream(
                table_ids=table_ids,
                sql_query=sql_query,
                db_uri=db_uri,
                ds_id=ds_id,
                bypassed_dq_sources=bypassed_dq_sources,
                default_schema_name=default_schema_name,
                output_format=output_format,
                dq_score_threshold=dq_score_threshold,
                chat_id=chat_id,
            )
            return ref if self.api.enable_streaming else next(ref)
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
        return """Get comprehensive custom field definitions for the Alation instance.

    This tool retrieves custom fields, built-in metadata fields, and built-in search facets
    with structured metadata and usage guidance. It's designed to help with data dictionary
    creation, metadata updates, and understanding field capabilities.

    Custom fields are user-defined metadata fields that organizations create to capture
    business-specific information beyond Alation's standard or built-in fields (title, description, stewards).

    WHEN TO USE:
    - To understand what custom metadata fields are available in the instance
    - To validate custom field names and types before bulk updates
    - Before generating data dictionary files that need to include custom field updates

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
    - name_plural: Display name shown in the UI (plural form, empty string if not applicable)"""

    @track_tool_execution()
    def run(
        self, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
        return """Generates comprehensive instructions for creating Alation Data Dictionary CSV files.

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

        Returns:
        Complete instruction set with formatting rules, validation schemas, and examples
        """

    @track_tool_execution()
    def run(self, chat_id: Optional[str] = None) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
        """
        Generate comprehensive data dictionary CSV formatting instructions.

        Automatically fetches current custom field definitions and provides complete
        formatting rules, validation schemas, and examples.

        Parameters:
            chat_id (optional): Chat session identifier

        Returns:
            Complete instruction set for creating data dictionary CSV files
        """
        try:
            ref = self.api.get_data_dictionary_instructions_stream(chat_id=chat_id)
            return ref if self.api.enable_streaming else next(ref)
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
        return """HELPER TOOL: Instructions for building signatures for low-level catalog tools.

This tool provides formatting guidance for the `signature` parameter used by
`get_context_by_id` and `bulk_retrieval` tools.

NOTE: If you're using `catalog_context_search_agent`, you don't need this tool.
Signatures are only needed for direct low-level tool access.

WHEN TO USE:
- User explicitly requests signature creation instructions
- Before calling `get_context_by_id` with a custom signature
- Before calling `bulk_retrieval` (signature is required)
- Need guidance on available object types and fields

PARAMETERS:
- chat_id (optional): Chat session identifier

RETURNS:
Complete signature creation instructions including templates, examples,
and best practices for validation and filter rules.
"""

    @track_tool_execution()
    def run(
        self, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
        return """WORKFLOW ORCHESTRATOR for controlled catalog data retrieval.

`catalog_context_search_agent` handles most catalog questions automatically and returns
Alation's processed response. Use `analyze_catalog_question` when you need direct access
to catalog objects or control over the search workflow.

WHEN TO USE:
- User explicitly requests "analyze_catalog_question" or this specific tool
- You need to chain multiple catalog/tool operations together
- You want control over which fields, filters, or object types to retrieve
- Building custom workflows
- You need direct access to catalog objects rather than a processed response

PARAMETERS:
- question (required): The catalog question to analyze
- chat_id (optional): Chat session identifier

RETURNS:
Step-by-step workflow instructions, tool selection guidance, and signature building tips
for using `get_context_by_id` or `bulk_retrieval` tools.
"""

    @track_tool_execution()
    def run(
        self, *, question: str, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
        return """PRIMARY ENTRY POINT: Search and discover data assets in the Alation catalog.

    Call this agent for ANY catalog search question. It automatically determines the optimal
    search strategy — semantic (search + filters) or bulk enumeration (filters only)—and handles
    complex queries without requiring manual tool orchestration.

    USE CASES:
    ✓ "Find sales-related tables" (semantic)
    ✓ "List all tables in finance schema" (bulk enumeration)
    ✓ "Tables with PII classification" (bulk enumeration)
    ✓ "Documentation about revenue" (semantic)
    ✓ "Endorsed tables from data source X" (bulk enumeration)
    ✓ "Columns containing customer data" (semantic)

    SUPPORTED OBJECT TYPES:
    tables, columns, schemas, queries, BI reports, documentation

    PARAMETERS:
    - message (required): Natural language description of what you're searching for
    - chat_id (optional): Chat session identifier for context-aware searches

    RETURNS:
    Contextually-aware search results with enriched metadata and relationships.
    """

    @track_tool_execution()
    def run(
        self, *, message: str, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
    def run(
        self, *, message: str, marketplace_id: str, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
    def run(
        self, *, message: str, data_product_id: str, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
        return """Retrieve all available data sources from the Alation catalog.

        This tool retrieves a list of all data sources available in the catalog.
        Each data source includes its ID, title, and URL.

        Example output:
            [
                {
                    "id": 15,
                    "title": "DQ INSIGHTS",
                    "url": "/data/15/"
                },
                {
                    "id": 20,
                    "title": "Sales Database",
                    "url": "/data/20/"
                }
            ]

        Parameters:
        - limit (optional, int): Maximum number of data sources to return (default: 100)
        - chat_id (optional, str): Chat session identifier

        Returns:
        List of available data sources with their metadata and connection information.
        """

    @track_tool_execution()
    def run(
        self, *, limit: int = 100, chat_id: Optional[str] = None
    ) -> Union[Generator[Dict[str, Any], None, None], Dict[str, Any]]:
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
