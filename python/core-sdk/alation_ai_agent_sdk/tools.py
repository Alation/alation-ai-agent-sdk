from typing import Dict, Any, Optional
import re
import logging
import requests
from requests.exceptions import RequestException

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


class GenerateDataProductTool:
    def __init__(self, api: AlationAPI):
        self.api = api
        self.name = self._get_name()
        self.description = self._get_description()
        self._cached_schema = None  # Cache the schema to avoid repeated requests

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

    def _fetch_schema_from_instance(self) -> Optional[str]:
        """
        Fetch the data product schema from the Alation instance.

        Returns:
            str: The schema content as YAML string, or None if fetch fails
        """
        if not self.api or not hasattr(self.api, 'base_url'):
            logger.warning("No API instance available to fetch schema")
            return None

        schema_url = f"{self.api.base_url}/static/swagger/specs/data_products/product_schema.yaml"

        try:
            logger.debug(f"Fetching data product schema from: {schema_url}")
            response = requests.get(schema_url, timeout=10)
            response.raise_for_status()

            schema_content = response.text
            logger.debug("Successfully fetched data product schema from instance")
            return schema_content

        except RequestException as e:
            logger.warning(f"Failed to fetch schema from {schema_url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching schema: {e}")
            return None

    def _get_schema_content(self) -> str:
        """
        Get the schema content, trying to fetch from instance first, then falling back to hardcoded version.
        """
        # Check cache first
        if self._cached_schema is not None:
            return self._cached_schema

        # Try to fetch from instance
        schema_content = self._fetch_schema_from_instance()

        if schema_content:
            # Cache the fetched schema
            self._cached_schema = schema_content
            return schema_content

        # If we get here, the fetch failed - raise an error
        raise AlationAPIError(
            "Failed to fetch data product schema from Alation instance",
            reason="Schema Fetch Failed",
            resolution_hint="Ensure your Alation instance is accessible and the schema endpoint is available. Check network connectivity and instance version.",
            alation_release_name=getattr(self.api, "alation_release_name", None),
            dist_version=getattr(self.api, "dist_version", None),
        )

    @staticmethod
    def _get_example_content() -> str:
        return """
    product:
      productId: "marketing.db.customer_360_view"
      version: "1.0"
      contactEmail: "data-gov-team@alation.com"
      contactName: "Data Governance Team"
      en:
        name: "Customer 360 View"
        shortDescription: "Comprehensive view of active customers combining CRM, sales, and support data"
        description: |
          A comprehensive, 360-degree view of our active customers. This product combines data from our CRM, sales, and support systems to provide a unified customer profile. It is the gold standard for all customer-related analytics.

          ## Key Concepts
          - **Active Customer:** A customer who has made a purchase in the last 12 months.
          - **Data Quality Note:** Customer names are not guaranteed to be unique. Use customer_id for joins.

          ## Relationships
          - `customer_profile(customer_id)` -> `customer_monthly_spend(customer_id)`

      deliverySystems:
        snowflake_prod:
          type: sql
          uri: "snowflake://company.snowflakecomputing.com/PROD_DB"

      recordSets:
        customer_profile:
          name: "customer_profile"
          displayName: "Customer Profile"
          description: "Core customer information and attributes"
          schema:
            - name: "customer_id"
              displayName: "Customer ID"
              type: "integer"
              description: "Unique identifier for the customer."
            - name: "full_name"
              displayName: "Full Name"
              type: "string"
              description: "Full name of the customer."
            - name: "email"
              displayName: "Email Address"
              type: "string"
              description: "Primary email address for the customer."
          dataAccess:
            - type: "sql"
              qualifiedName:
                schema: "marketing"
                table: "customer_profile"

        customer_monthly_spend:
          name: "customer_monthly_spend"
          displayName: "Customer Monthly Spend"
          description: "Monthly spending patterns per customer"
          schema:
            - name: "customer_id"
              displayName: "Customer ID"
              type: "integer"
              description: "Foreign key to the customer_profile record set."
            - name: "month_year"
              displayName: "Month Year"
              type: "date"
              description: "The month and year for this spending record."
            - name: "total_spend_usd"
              displayName: "Total Spend (USD)"
              type: "number"
              description: "Total amount spent by the customer in that month, in USD."
          sample:
            type: "mock"
            data: |
              customer_id,month_year,total_spend_usd
              123,2024-01-01,1250.50
              124,2024-01-01,890.25
              123,2024-02-01,1100.00
          dataAccess:
            - type: "sql"
              qualifiedName:
                schema: "marketing"
                table: "customer_monthly_spend"
    """

    @staticmethod
    def _get_prompt_instructions() -> str:
        return """
    You are an AI assistant for Alation. You have been provided with the current Alation Data Product schema and a valid example. Your task is to convert user-provided semantic layers or data specifications into valid Alation Data Product YAML files.

    **CRITICAL: DO NOT HALLUCINATE OR ADD ANY INFORMATION NOT PROVIDED BY THE USER**

    **Your instructions are:**
    1. You **MUST** strictly adhere to the provided schema below.
    2. You **MUST** use the provided example below as a template for style and format.
    3. **NEVER ADD, INVENT, OR HALLUCINATE ANY REALISTIC-LOOKING INFORMATION not present in the user's input. This includes:**
       - Actual contact emails, names, or personal information
       - Actual database URIs, connection strings, or system details
       - Business logic or descriptions beyond what the user specified
       - Access instructions or organizational details
       - Sample data or mock values
    4. **Field Handling Rules:**
       - **Required fields**: If not provided by user, use placeholders like "TBD"
       - **Optional fields**: If not provided by user, omit the field entirely
       - **Never generate realistic-looking values** for any field type
    5. **Specific Field Guidelines:**
       - contactEmail: Use "TBD" if not provided (required field)
       - contactName: Use "TBD" if not provided (required field)  
       - sample: Omit entirely if not provided (optional field)
       - logoUrl: Omit entirely if not provided (optional field)
    6. The final output must be a single, valid YAML file that passes schema validation.

    **Key Schema Requirements:**
    - `recordSets` is an OBJECT (not array) where each key is a record set identifier
    - Each record set must have `name`, `displayName`, `description`, `schema`, and optionally `sample` and `dataAccess`
    - Schema fields must include `name`, `displayName`, `description`, and `type`
    - `deliverySystems` is required and should be an object with at least one delivery system
    - `en.name` is required, `en.description` and `en.shortDescription` are separate fields
    - `sample` section is optional - omit entirely if user doesn't provide actual sample data
    - `logoUrl` is optional - omit entirely if user doesn't provide it
    - Optional fields should only be included when user explicitly provides values
    - **REMINDER: Use only information from user input - NO HALLUCINATIONS**

    ---
    **THE SCHEMA:**
    {schema}

    ---
    **THE EXAMPLE:**
    {example}

    **FINAL REMINDER: Only convert what the user provided. For required fields, use "TBD" placeholders when missing. For optional fields, omit entirely when not provided. Never invent realistic-looking contact details, system information, sample data, or other metadata.**
    """

    def run(self) -> str:
        """
        Assembles and returns the complete instructional prompt for creating
        an Alation Data Product using the current schema from the instance.
        """
        schema_content = self._get_schema_content()
        example_content = self._get_example_content()
        prompt_instructions = self._get_prompt_instructions()

        final_instructions = prompt_instructions.format(
            schema=schema_content,
            example=example_content
        )
        return final_instructions
