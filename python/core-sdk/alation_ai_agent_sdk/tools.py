import re
import logging
import requests
import time
from requests.exceptions import RequestException

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
        Retrieves contextual information from Alation's data catalog using natural language questions.

        This tool translates natural language questions into catalog queries and returns structured data about:
        - Tables (including description, common joins, common filters, schema (columns))
        - Columns/Attributes (with types and sample values)
        - Documentation (Includes various object types like articles, glossaries, document folders, documents)
        - Queries (includes description and sql content)

        IMPORTANT: Always pass the exact, unmodified user question to this tool. The internal API 
        handles query processing, rewriting, and optimization automatically.

        Examples:
        - "What tables contain customer information?"
        - "Find documentation about our data warehouse" 
        - "What are the commonly joined tables with customer_profile?"
        - "Can you explain the difference between loan type and loan term?"

        The tool returns JSON-formatted metadata relevant to your question, enabling data discovery
        and exploration through conversational language.

        Parameters:
        - question (string): The exact user question, unmodified and uninterpreted
        - signature (JSON, optional): A JSON specification of which fields to include in the response
          This allows customizing the response format and content.

        Signature format:
        ```json
            {
              "{object_type}": {
                "fields_required": ["field1", "field2"], //List of fields
                "fields_optional": ["field3", "field4"], //List of fields
                "search_filters": {
                  "domain_ids": [123, 456], //List of integer values
                  "flags": ["Endorsement", "Deprecation", "Warning"],  // Only these three values are supported
                  "fields": {
                    "tag_ids": [789], //List of integer values
                    "ds": [101], //List of integer values
                    ...
                  }
                },
                "child_objects": {
                  "{child_type}": {
                    "fields": ["field1", "field2"] //List of fields
                  }
                }
              }
            }
"""

    @min_alation_version("2025.1.2")
    def run(self, question: str, signature: Optional[Dict[str, Any]] = None):
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

    def run(self, product_id: Optional[str] = None, query: Optional[str] = None):
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
        return """Fetches bulk sets of data catalog objects without requiring questions.
    
    Parameters:
    - signature (required): A dictionary containing object type configurations
    
    USE THIS TOOL FOR:
    - Getting bulk objects based on signature (e.g. "fetch objects based on this signature", "get objects matching these criteria")

    DON'T USE FOR:
    - Answering specific questions about data (use alation_context instead)
    - Exploratory "what" or "how" questions
    - When you need conversational context
    
    REQUIRES: Signature parameter defining object types, fields, and filters
    
    CAPABILITIES:
    - SUPPORTS MULTIPLE OBJECT TYPES: table, column, schema, query
    - Documentation objects not supported.
    
    USAGE EXAMPLES:
     - Single type: bulk_retrieval(signature = {"table": {"fields_required": ["name", "url"], "search_filters": {"flags": ["Endorsement"]}, "limit": 10}})
     - Multiple types: bulk_retrieval(signature = {"table": {"fields_required": ["name", "url"], "limit": 10}, "column": {"fields_required": ["name", "data_type"], "limit": 50}})
     - With relationships: bulk_retrieval(signature = {"table": {"fields_required": ["name", "columns"], "child_objects": {"columns": {"fields": ["name", "data_type"]}}, "limit": 10}})
    """

    def run(self, signature: Optional[Dict[str, Any]] = None):
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

    def run(
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

    def run(self, custom_field_values: list[CatalogAssetMetadataPayloadItem]) -> dict:
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

    def run(self, job_id: int) -> dict:
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
            Check data quality of SQL queries or tables before/after execution.
            
            **Call this function when:**
            - User directly asks to "check data quality"
            - User requests to "validate data quality" or "assess quality"
            - User asks "is this data reliable/trustworthy?"
            - User says "run data quality check" or similar explicit request
            
            **Required:** Either table_ids OR sql_query
            **Key parameters:**
            - sql_query: SQL to analyze for quality issues
            - table_ids: List of table IDs (max 30) - use alation_context to get IDs first
            - ds_id: Required with table_ids, datasource ID from Alation
            - db_uri: Database URI, alternative to ds_id for SQL analysis
            - output_format: "JSON" (default) or "YAML_MARKDOWN" for readable reports
            - dq_score_threshold: Quality threshold (0-100), tables below this are flagged
            
            **Parameter combinations:**
            1. sql_query + ds_id (recommended for SQL validation)
            2. sql_query + db_uri (when ds_id unknown)
            3. table_ids (for specific table validation)
            
            Returns quality scores, issues, and recommendations in specified format. """

    def run(
        self,
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
                    logger.info("Non-admin user detected, providing built-in fields only")
                    custom_fields = []
                else:
                    raise

            # Generate the comprehensive instructions
            instructions = build_optimized_instructions(custom_fields)
            return instructions

        except AlationAPIError as e:
            return f"Error generating instructions: {e}"


def csv_str_to_tool_list(tool_env_var: Optional[str] = None) -> List[str]:
    if tool_env_var is None:
        return []
    uniq = set()
    if tool_env_var:
        for tool_str in tool_env_var.split(","):
            tool_str = tool_str.strip()
            uniq.add(tool_str)
    return list(uniq)
