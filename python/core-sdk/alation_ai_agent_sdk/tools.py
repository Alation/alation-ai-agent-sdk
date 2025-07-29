from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)
from alation_ai_agent_sdk.api import AlationAPI, AlationAPIError, CatalogAssetMetadataPayloadItem


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
    """

    def parse(ver):
        match = re.search(r"(\d+\.\d+\.\d+)", ver)
        ver = match.group(1) if match else ver
        parts = [int(p) for p in ver.split(".")]
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


class GetDataProductTool:
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


class UpdateCatalogAssetMetadataTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = "update_catalog_asset_metadata"
        self.description = """
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
        self.name = "check_job_status"
        self.description = """
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
