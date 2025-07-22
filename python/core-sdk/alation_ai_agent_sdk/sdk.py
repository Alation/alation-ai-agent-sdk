from typing import Dict, Any, Optional

from .api import AlationAPI, AlationAPIError, AuthParams, CatalogAssetMetadataPayloadItem
from .tools import (
    AlationContextTool,
    AlationBulkRetrievalTool,
    GetDataProductTool,
    UpdateCatalogAssetMetadataTool,
    CheckJobStatusTool,
)


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
        dist_version: Optional[str] = None,
    ):
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string.")

        if not auth_method or not isinstance(auth_method, str):
            raise ValueError("auth_method must be a non-empty string.")

        # Delegate validation of auth_params to AlationAPI
        self.api = AlationAPI(
            base_url=base_url,
            auth_method=auth_method,
            auth_params=auth_params,
            dist_version=dist_version,
        )
        self.context_tool = AlationContextTool(self.api)
        self.bulk_retrieval_tool = AlationBulkRetrievalTool(self.api)
        self.data_product_tool = GetDataProductTool(self.api)
        self.update_catalog_asset_metadata_tool = UpdateCatalogAssetMetadataTool(self.api)
        self.check_job_status_tool = CheckJobStatusTool(self.api)

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

    def get_tools(self):
        return [
            self.context_tool,
            self.bulk_retrieval_tool,
            self.data_product_tool,
            self.update_catalog_asset_metadata_tool,
            self.check_job_status_tool,
        ]
