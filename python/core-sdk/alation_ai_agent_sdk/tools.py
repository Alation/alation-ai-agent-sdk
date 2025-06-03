from typing import Dict, Any, Optional

from alation_ai_agent_sdk.api import AlationAPI, AlationAPIError


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
        Retrieve one or more data products that match the user query or product ID.

        This tool allows users to search for data products using natural language queries or directly retrieve a data product by its productId. It interacts with the appropriate Alation Data Products API endpoints.

        Example:
        - "Which data products contain recent sales information?"
        - "Get data product with ID sales.product:2024"

        Parameters:
        - query_or_product_id (string): The user query (free text) or a productId string (matching the pattern '^[.\\w:-]+$').

        The tool returns JSON-formatted metadata about the matching data products, or a single data product if a productId is provided.
        """

    def run(self, query_or_product_id: str):
        try:
            return self.api.get_data_products(query_or_product_id)
        except AlationAPIError as e:
            return {"error": e.to_dict()}
