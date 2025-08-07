import logging
import requests
import time
from requests.exceptions import RequestException

from typing import (
    Optional,
)

from alation_ai_agent_sdk.api import (
    AlationAPIError,
)

logger = logging.getLogger(__name__)


def _fetch_schema_from_instance(self) -> Optional[str]:
    """
    Fetch the data product schema from the Alation instance.

    Returns:
        str: The schema content as YAML string, or None if fetch fails
    """
    if not self.api or not hasattr(self.api, "base_url"):
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


def get_schema_content(self) -> str:
    """
    Get the schema content, trying to fetch from instance first, then falling back to hardcoded version.
    """
    # 1. Check if the cache exists and is still valid
    if self._cached_schema:
        schema_content, cached_at = self._cached_schema
        if time.time() - cached_at < self.CACHE_TTL_SECONDS:
            return schema_content
        else:
            logger.info("Schema cache has expired. Re-fetching.")

    # 2. If cache is empty or expired, fetch from instance
    schema_content = _fetch_schema_from_instance(self)

    if schema_content:
        # 3. If fetch is successful, update the cache with the new content and timestamp
        self._cached_schema = (schema_content, time.time())
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
def get_example_content() -> str:
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
def get_prompt_instructions() -> str:
    return """
        You are a highly specialized AI assistant for Alation. Your single, critical mission is to **CONVERT** user-provided information into a valid Alation Data Product YAML file. You are a literal translator, not a creator.

        **--- CORE DIRECTIVES ---**

        **1. ZERO HALLUCINATION & INVENTION**
        This is the most important rule. You are strictly **PROHIBITED** from inventing, guessing, or inferring any information not explicitly provided by the user.
        - If a user provides a column name but no description, the output YAML for that column **MUST NOT** have a `description` field.
        - If a user provides a table name but no `displayName`, the output YAML for that table **MUST NOT** have a `displayName` field.
        - **DO NOT** create realistic-looking sample data, contact details, system information, or descriptions.
        - If the information is not in the user's input, it **MUST NOT** be in the output YAML.

        **2. STRICT SCHEMA ADHERENCE**
        The final output **MUST** be a valid YAML file that perfectly conforms to the provided Alation Data Product schema.

        **3. DATA CLEANING & FORMATTING**
        You are responsible for formatting the input data correctly for the YAML output.
        - **Clean all descriptions:** All `description` fields, for both record sets and columns, **MUST** be cleaned of raw HTML tags (`<p>`, `<div>`, `<a>`, `<b>`, etc.). Convert them to clean, readable plain text or Markdown.
            - Example Input: `<p>This is a <b>description</b>.</p>`
            - Correct YAML Output: `description: "This is a description."`
            
        **4. COMPLETE DATA PRESERVATION**
        When creating data products:
        - INCLUDE ALL TABLES: Every table must be included as a record set in the data product,
        - INCLUDE ALL COLUMNS: Every column from each table must be included in the record set schema with its complete metadata
        - PRESERVE ALL RELATIONSHIPS: All common_joins and relationship information must be documented in the data product.
        - MAINTAIN FULL CONTEXT: Do not selectively choose subsets - include the complete data ecosystem provided. 
        
        **5:  DATA COMPLETENESS VALIDATION**
        Before finalizing the YAML, verify:
        
        ✅ ALL source tables are represented as record sets
        ✅ ALL columns from source are included in schemas
        ✅ ALL relationship information is documented
        ✅ No important context has been omitted
        
        **--- FIELD HANDLING RULES ---**

        * **MANDATORY FIELDS (Use "TBD" if missing):**
            If the user does not provide a value for a mandatory field, you **MUST** use the exact string "TBD" as a placeholder.
            - `productId`: (e.g., "TBD")
            - `version`: (e.g., "TBD")
            - `contactEmail`: (e.g., "TBD")
            - `contactName`: (e.g., "TBD")
            - `en.name`: The name of the data product provided by the user (e.g., "Finance data product"). If not provided at all, use "TBD".

        * **OPTIONAL FIELDS (Omit if missing):**
            If the user does not provide a value for ANY optional field (like `displayName`, `description`, `shortDescription`, etc.), you **MUST** omit that field entirely from the YAML. This is not a suggestion; it is a command with no exceptions.

        * **EXAMPLE: Handling Optional Fields**
            Imagine the user provides only the name `order_id` and its type. They provide no `displayName` and no `description`.

            ✅ **CORRECT (Omit all optional fields):**
            ```yaml
            - name: "order_id"
            type: "integer"
            ```

            ❌ **INCORRECT (Generating a `displayName` or `description`):**
            ```yaml
            - name: "order_id"
            displayName: "Order ID" # <-- FORBIDDEN (displayName was not provided)
            type: "integer"
            description: "Unique identifier for the sales order." # <-- FORBIDDEN (description was not provided)
            ```

        ---
        **THE SCHEMA:**
        {schema}

        ---
        **THE EXAMPLE (FOR STRUCTURE REFERENCE ONLY):**
        {example}

        **FINAL REMINDER:** Your only goal is to mechanically convert the user's input. Clean the data as instructed. For mandatory fields without input, use "TBD". For **ALL** optional fields without input, **OMIT THEM**. There are no exceptions.
        """
