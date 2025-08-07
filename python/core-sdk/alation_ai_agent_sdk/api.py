import datetime
import logging
import urllib.parse
import json
import requests
import requests.exceptions
from typing import Any, Dict, List, Optional, Union
from http import HTTPStatus
from uuid import uuid4
from alation_ai_agent_sdk.lineage_filtering import filter_graph
from .types import (
    UserAccountAuthParams,
    ServiceAccountAuthParams,
    AuthParams,
    CatalogAssetMetadataPayloadItem,
)
from .errors import AlationAPIError, AlationErrorClassifier

from alation_ai_agent_sdk.lineage import (
    LineageBatchSizeType,
    LineageDesignTimeType,
    LineageGraphProcessingOptions,
    LineageGraphProcessingType,
    LineageKeyTypeType,
    LineageOTypeFilterType,
    LineagePagination,
    LineageRootNode,
    LineageExcludedSchemaIdsType,
    LineageTimestampType,
    LineageDirectionType,
)


AUTH_METHOD_USER_ACCOUNT = "user_account"
AUTH_METHOD_SERVICE_ACCOUNT = "service_account"

logger = logging.getLogger(__name__)


class CatalogAssetMetadataPayloadBuilder:
    """
    Builder class for constructing and validating payloads for update_catalog_asset_metadata.
    Ensures all required fields are present and valid for each object in the payload.
    """

    REQUIRED_FIELDS = {"oid", "otype", "field_id", "value"}
    ALLOWED_OTYPES = {"glossary_v3", "glossary_term"}
    FIELD_ID_TYPE_MAP = {
        3: str,  # TEXT
        4: str,  # RICH_TEXT
    }

    @classmethod
    def validate(cls, obj: CatalogAssetMetadataPayloadItem) -> None:
        missing = cls.REQUIRED_FIELDS - obj.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        if obj["otype"] not in cls.ALLOWED_OTYPES:
            raise ValueError(f"Invalid otype: {obj['otype']}. Allowed: {cls.ALLOWED_OTYPES}")
        if obj["field_id"] not in cls.FIELD_ID_TYPE_MAP:
            raise ValueError(
                f"Invalid field_id: {obj['field_id']}. Allowed: {list(cls.FIELD_ID_TYPE_MAP.keys())}"
            )
        expected_type = cls.FIELD_ID_TYPE_MAP[obj["field_id"]]
        if not isinstance(obj["value"], expected_type):
            raise ValueError(
                f"field_id {obj['field_id']} requires a value of type {expected_type.__name__}"
            )

    @classmethod
    def build(
        cls, items: list[CatalogAssetMetadataPayloadItem]
    ) -> list[CatalogAssetMetadataPayloadItem]:
        if not isinstance(items, list):
            raise ValueError("Payload must be a list of objects")
        validated = []
        for i, obj in enumerate(items):
            try:
                cls.validate(obj)
            except Exception as e:
                raise ValueError(f"Validation failed for item {i}: {e}")
            validated.append(obj)
        return validated


class AlationAPI:
    """
    Client for interacting with the Alation API.
    This class manages authentication (via refresh token or service account)
    and provides methods to retrieve context-specific information from the Alation catalog.

    Attributes:
        base_url (str): Base URL for the Alation instance
        auth_method (str): Authentication method ("user_account" or "service_account")
        auth_params (AuthParams): Parameters required for the chosen authentication method
    """

    def __init__(
        self,
        base_url: str,
        auth_method: str,
        auth_params: AuthParams,
        dist_version: Optional[str] = None,
        skip_instance_info: Optional[bool] = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.auth_method = auth_method
        self.is_cloud = None
        self.alation_release_name = None
        self.alation_version_info = None
        self.dist_version = dist_version

        # Validate auth_method and auth_params
        if auth_method == AUTH_METHOD_USER_ACCOUNT:
            if not isinstance(auth_params, UserAccountAuthParams):
                raise ValueError(
                    "For 'user_account' authentication, provide a tuple with (user_id: int, refresh_token: str)."
                )
            self.user_id, self.refresh_token = auth_params

        elif auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            if not isinstance(auth_params, ServiceAccountAuthParams):
                raise ValueError(
                    "For 'service_account' authentication, provide a tuple with (client_id: str, client_secret: str)."
                )
            self.client_id, self.client_secret = auth_params

        else:
            raise ValueError("auth_method must be either 'user_account' or 'service_account'.")

        logger.debug(f"AlationAPI initialized with auth method: {self.auth_method}")

        if not skip_instance_info:
            self._fetch_and_cache_instance_info()

    def _fetch_and_cache_instance_info(self):
        """
        Fetches instance info (license and version) after authentication and caches in memory.
        """
        self._with_valid_token()
        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }
        try:
            # License info
            license_url = f"{self.base_url}/api/v1/license"
            license_resp = requests.get(license_url, headers=headers, timeout=10)
            license_resp.raise_for_status()
            license_data = license_resp.json()
            self.is_cloud = license_data.get("is_cloud", None)
            self.alation_license_info = license_data
        except Exception as e:
            logger.warning(f"Could not fetch license info: {e}")
            self.is_cloud = None
            self.alation_license_info = None
        try:
            # Version info
            version_url = f"{self.base_url}/full_version"
            version_resp = requests.get(version_url, timeout=10)
            version_resp.raise_for_status()
            version_data = version_resp.json()
            self.alation_release_name = version_data.get("ALATION_RELEASE_NAME", None)
            self.alation_version_info = version_data
        except Exception as e:
            logger.warning(f"Could not fetch version info: {e}")
            self.alation_release_name = None
            self.alation_version_info = None

    def _handle_request_error(self, exception: requests.RequestException, context: str):
        """Utility function to handle request exceptions."""

        alation_release_name = getattr(self, "alation_release_name", None)
        dist_version = getattr(self, "dist_version", None)

        if isinstance(exception, requests.exceptions.Timeout):
            raise AlationAPIError(
                f"Request to {context} timed out after 60 seconds.",
                reason="Timeout Error",
                resolution_hint="Ensure the server is reachable and try again later.",
                help_links=["https://developer.alation.com/"],
                alation_release_name=alation_release_name,
                dist_version=dist_version,
            )

        status_code = getattr(exception.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
        response_text = getattr(exception.response, "text", "No response received from server")
        try:
            parsed = (
                exception.response.json()
                if exception.response is not None
                else {"error": response_text}
            )
        except (json.JSONDecodeError, ValueError) as parse_exc:
            parsed = {"error": response_text}
        meta = AlationErrorClassifier.classify_catalog_error(status_code, parsed)
        raise AlationAPIError(
            f"HTTP error during {context}: {meta['reason']}",
            original_exception=exception,
            status_code=status_code,
            response_body=parsed,
            reason=meta["reason"],
            resolution_hint=meta["resolution_hint"],
            help_links=meta["help_links"],
            alation_release_name=alation_release_name,
            dist_version=dist_version,
        )

    def _generate_access_token_with_refresh_token(self):
        """
        Generate a new access token using User ID and Refresh Token.
        """

        url = f"{self.base_url}/integration/v1/createAPIAccessToken/"
        payload = {
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
        }
        logger.debug(f"Generating access token using refresh token for user_id: {self.user_id}")

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            self._handle_request_error(e, "access token generation")

        try:
            data = response.json()
        except ValueError:
            raise AlationAPIError(
                "Invalid JSON in access token response",
                status_code=response.status_code,
                response_body=response.text,
                reason="Token Response Error",
                resolution_hint="Contact Alation support; server returned non-JSON body.",
                help_links=["https://developer.alation.com/"],
            )

        if data.get("status") == "failed" or "api_access_token" not in data:
            meta = AlationErrorClassifier.classify_token_error(response.status_code, data)
            raise AlationAPIError(
                f"Logical failure or missing token in access token response from {url}",
                status_code=response.status_code,
                response_body=str(data),
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

        self.access_token = data["api_access_token"]
        logger.debug("Access token generated from refresh token")

    def _generate_jwt_token(self):
        """
        Generate a new JSON Web Token (JWT) using Client ID and Client Secret.
        Documentation: https://developer.alation.com/dev/reference/createtoken
        """
        url = f"{self.base_url}/oauth/v2/token/"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }
        logger.debug("Generating JWT token")
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            self._handle_request_error(e, "JWT token generation")

        try:
            data = response.json()
        except ValueError:
            raise AlationAPIError(
                "Invalid JSON in JWT token response",
                status_code=response.status_code,
                response_body=response.text,
                reason="Token Response Error",
                resolution_hint="Contact Alation support; server returned non-JSON body.",
                help_links=["https://developer.alation.com/"],
            )

        if "access_token" not in data:
            meta = AlationErrorClassifier.classify_token_error(response.status_code, data)
            raise AlationAPIError(
                f"Access token missing in JWT API response from {url}",
                status_code=response.status_code,
                response_body=str(data),
                reason=meta.get("reason", "Malformed JWT Response"),
                resolution_hint=meta.get(
                    "resolution_hint", "Ensure client_id and client_secret are correct."
                ),
                help_links=meta["help_links"],
            )

        self.access_token = data["access_token"]
        logger.debug("JWT token generated from client ID and secret")

    def _generate_new_token(self):

        logger.info("Access token is invalid or expired. Attempting to generate a new one.")
        if self.auth_method == AUTH_METHOD_USER_ACCOUNT:
            self._generate_access_token_with_refresh_token()
        elif self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            self._generate_jwt_token()
        else:
            raise AlationAPIError(
                "Invalid authentication method configured.",
                reason="Internal SDK Error",
                resolution_hint="SDK improperly configured.",
            )

    def _is_access_token_valid(self) -> bool:
        """
        Check if the access token is valid by making a request to the validation endpoint.
        Returns True if valid, False if invalid or revoked.

        """

        url = f"{self.base_url}/integration/v1/validateAPIAccessToken/"
        payload = {"api_access_token": self.access_token, "user_id": self.user_id}
        headers = {"accept": "application/json", "content-type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)

            if status_code is HTTPStatus.UNAUTHORIZED:
                return False

            response_text = getattr(e.response, "text", "No response received from server")
            parsed = {"error": response_text}
            meta = AlationErrorClassifier.classify_token_error(status_code, parsed)

            raise AlationAPIError(
                "Internal error during access token generation",
                original_exception=e,
                status_code=status_code,
                response_body=parsed,
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

        return True

    def _is_jwt_token_valid(self) -> bool:
        """
        Payload when token is active: status: 200
            {
                "active": true,
                ...
            }
        Payload when token is inactive: status: 200
            {
                "active": false,
            }
        """

        url = f"{self.base_url}/oauth/v2/introspect/?verify_token=true"

        payload = {
            "token": self.access_token,
            "token_type_hint": "access_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("active", False)
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
            response_text = getattr(e.response, "text", "No response received from server")
            parsed = {"error": response_text}
            meta = AlationErrorClassifier.classify_token_error(status_code, parsed)

            raise AlationAPIError(
                "Error validating JWT token",
                original_exception=e,
                status_code=status_code,
                response_body=parsed,
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )
        except ValueError as e:
            raise AlationAPIError(
                "Invalid JSON in JWT token validation response",
                reason="Malformed Response",
                resolution_hint="The server returned a non-JSON response. Contact support if this persists.",
                help_links=["https://developer.alation.com/"],
                original_exception=e,
            )

    def _token_is_valid_on_server(self):
        try:
            if self.auth_method == AUTH_METHOD_USER_ACCOUNT:
                return self._is_access_token_valid()
            elif self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
                return self._is_jwt_token_valid()
        except Exception as e:
            logger.error(f"Error validating token on server: {e}")
            return False

    def _with_valid_token(self):
        """
        Ensures a valid access token is available, generating one if needed.
        Check validity on server (other services can revoke and invalidate tokens)
        """
        try:
            if self.access_token and self._token_is_valid_on_server():
                logger.debug("Access token is valid on server")
                return
        except Exception as e:
            logger.error(f"Error checking token validity: {e}")

        self._generate_new_token()

    def get_context_from_catalog(self, query: str, signature: Optional[Dict[str, Any]] = None):
        """
        Retrieve contextual information from the Alation catalog based on a natural language query and signature.
        """
        if not query:
            raise ValueError("Query cannot be empty")

        self._with_valid_token()

        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }

        params = {"question": query, "mode": "search"}
        if signature:
            params["signature"] = json.dumps(signature, separators=(",", ":"))

        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{self.base_url}/integration/v2/context/?{encoded_params}"

        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()

        except requests.RequestException as e:
            self._handle_request_error(e, "catalog search")

        try:
            return response.json()
        except ValueError:
            raise AlationAPIError(
                message="Invalid JSON in catalog response",
                status_code=response.status_code,
                response_body=response.text,
                reason="Malformed Response",
                resolution_hint="The server returned a non-JSON response. Contact support if this persists.",
                help_links=["https://developer.alation.com/"],
            )

    def get_bulk_objects_from_catalog(self, signature: Dict[str, Any]):
        """
        Retrieve bulk objects from the Alation catalog based on signature specifications.
        Uses the context API in bulk mode without requiring a natural language question.
        """
        if not signature:
            raise ValueError("Signature cannot be empty for bulk retrieval")

        self._with_valid_token()

        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }

        params = {"mode": "bulk", "signature": json.dumps(signature, separators=(",", ":"))}

        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{self.base_url}/integration/v2/context/?{encoded_params}"

        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()

        except requests.RequestException as e:
            self._handle_request_error(e, "bulk catalog retrieval")

        try:
            return response.json()
        except ValueError:
            raise AlationAPIError(
                message="Invalid JSON in bulk catalog response",
                status_code=response.status_code,
                response_body=response.text,
                reason="Malformed Response",
                resolution_hint="The server returned a non-JSON response. Contact support if this persists.",
                help_links=["https://developer.alation.com/dev/reference/getaggregatedcontext"],
            )

    def _fetch_marketplace_id(self, headers: Dict[str, str]) -> str:
        """Fetch and return the marketplace ID."""
        marketplace_url = f"{self.base_url}/api/v1/setting/marketplace/"
        try:
            response = requests.get(marketplace_url, headers=headers, timeout=30)
            response.raise_for_status()
            marketplace_data = response.json()
            marketplace_id = marketplace_data.get("default_marketplace")
            if not marketplace_id:
                raise AlationAPIError(
                    message="Marketplace ID not found in response",
                    reason="Missing Marketplace ID",
                )
            return marketplace_id
        except requests.RequestException as e:
            self._handle_request_error(e, "fetching marketplace ID")

    def get_data_products(
        self, product_id: Optional[str] = None, query: Optional[str] = None
    ) -> dict:
        """
        Retrieve Alation Data Products by product id or free-text search.

        Args:
            product_id (str, optional): product id for direct lookup.
            query (str, optional): Free-text search query.

        Returns:
            dict: Contains 'instructions' (string) and 'results' (list of data product dicts).

        Raises:
            ValueError: If neither product_id nor query is provided.
            AlationAPIError: On network, API, or response errors.
        """
        self._with_valid_token()
        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }

        if product_id:
            # Fetch data product by ID
            url = f"{self.base_url}/integration/data-products/v1/data-product/{product_id}/"
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == HTTPStatus.NOT_FOUND:
                    return {
                        "instructions": "The product ID provided does not exist. Please verify the ID and try again.",
                        "results": [],
                    }
                response.raise_for_status()
                response_data = response.json()
                if isinstance(response_data, dict):
                    instructions = f"The following is the complete specification for data product '{product_id}'."
                    return {"instructions": instructions, "results": [response_data]}
                return {
                    "instructions": "No data products found for the given product ID.",
                    "results": [],
                }
            except requests.RequestException as e:
                self._handle_request_error(e, f"fetching data product by id: {product_id}")

        elif query:
            # Fetch marketplace ID if not cached
            if not hasattr(self, "marketplace_id"):
                self.marketplace_id = self._fetch_marketplace_id(headers)

            # Search data products by query
            url = f"{self.base_url}/integration/data-products/v1/search-internally/{self.marketplace_id}/"
            try:
                response = requests.post(
                    url, headers=headers, json={"user_query": query}, timeout=30
                )
                response.raise_for_status()
                response_data = response.json()
                if isinstance(response_data, list) and response_data:
                    instructions = (
                        f"Found {len(response_data)} data products matching your query. "
                        "The following contains summary information (name, id, description, url) for each product. "
                        "To get complete specifications, call this tool again with a specific product_id."
                    )
                    results = [
                        {
                            "id": product["product"]["product_id"],
                            "name": product["product"]["spec_json"]["product"]["en"]["name"],
                            "description": product["product"]["spec_json"]["product"]["en"][
                                "description"
                            ],
                            "url": f"{self.base_url}/app/marketplace/{self.marketplace_id}/data-product/{product['product']['product_id']}/",
                        }
                        for product in response_data
                    ]
                    return {"instructions": instructions, "results": results}
                return {
                    "instructions": "No data products found for the given query.",
                    "results": [],
                }
            except requests.RequestException as e:
                self._handle_request_error(e, f"searching data products with query: {query}")

        else:
            raise ValueError(
                "You must provide either a product_id or a query to search for data products."
            )

    def get_bulk_lineage(
        self,
        root_nodes: List[LineageRootNode],
        direction: LineageDirectionType,
        limit: int,
        batch_size: LineageBatchSizeType,
        processing_mode: LineageGraphProcessingType,
        show_temporal_objects: bool,
        design_time: LineageDesignTimeType,
        max_depth: int,
        excluded_schema_ids: LineageExcludedSchemaIdsType,
        allowed_otypes: LineageOTypeFilterType,
        time_from: LineageTimestampType,
        time_to: LineageTimestampType,
        key_type: LineageKeyTypeType,
        pagination: Optional[LineagePagination] = None,
    ) -> dict:
        """
        Fetch lineage information from Alation's catalog for a given object / root node.

        Args:
            root_nodes (List[LineageRootNode]): The root nodes to start lineage from.
            direction (LineageDirectionType): The direction of lineage to fetch, either "upstream" or "downstream".
            limit (int, optional): The maximum number of nodes to return. Defaults to the maximum 1,000.
            batch_size (int, optional): The size of each batch for chunked processing. Defaults to 1,000.
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
        # Filter out any incompatible options
        if limit > 1000:
            raise ValueError("limit cannot exceed 1,000.")
        if allowed_otypes is not None:
            if processing_mode != LineageGraphProcessingOptions.COMPLETE:
                raise ValueError("allowed_otypes is only supported in 'complete' processing mode.")
            if len(allowed_otypes) == 0:
                raise ValueError("allowed_otypes cannot be empty list.")
        if pagination is not None and processing_mode == LineageGraphProcessingOptions.COMPLETE:
            raise ValueError("pagination is only supported in 'chunked' processing mode.")

        self._with_valid_token()

        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }

        lineage_request_dict = {
            "key_type": key_type,
            "root_nodes": root_nodes,
            "direction": direction,
            "limit": limit,
            "filters": {
                "depth": max_depth,
                "time_filter": {
                    "from": time_from,
                    "to": time_to,
                },
                "schema_filter": excluded_schema_ids,
                "design_time": design_time,
            },
            "request_id": pagination.get("request_id") if pagination else uuid4().hex,
            "cursor": pagination.get("cursor", 0) if pagination else 0,
            "batch_size": (
                limit
                if processing_mode == LineageGraphProcessingOptions.COMPLETE
                else pagination.get("batch_size", limit) if pagination else batch_size
            ),
        }
        if show_temporal_objects:
            lineage_request_dict["filters"]["temp_filter"] = show_temporal_objects
        url = f"{self.base_url}/integration/v2/bulk_lineage/"
        try:
            response = requests.post(url, headers=headers, json=lineage_request_dict, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            if (
                "graph" in response_data
                and processing_mode == LineageGraphProcessingOptions.COMPLETE
            ):
                if allowed_otypes is not None:
                    allowed_otypes_set = set(allowed_otypes)
                    response_data["graph"] = filter_graph(
                        response_data["graph"], allowed_otypes_set
                    )
            request_id = response_data.get("request_id", "")
            # Deliberately Pascal cased to match implementation. We'll change it to be consistent for anything
            # invoking the tool.
            pagination = response_data.get("Pagination", None)
            if pagination is not None:
                new_pagination = {
                    "request_id": request_id,
                    "cursor": pagination.get("cursor", 0),
                    "batch_size": pagination.get("batch_size", batch_size),
                    "has_more": pagination.get("has_more", False),
                }
                response_data["pagination"] = new_pagination
                del response_data["Pagination"]
                del response_data["request_id"]
            response_data["direction"] = direction
            return response_data
        except requests.RequestException as e:
            self._handle_request_error(
                e, f"getting lineage for: {json.dumps(lineage_request_dict)}"
            )

    def update_catalog_asset_metadata(
        self, custom_field_values: list[CatalogAssetMetadataPayloadItem]
    ) -> dict:
        """
        Updates metadata for one or more Alation catalog assets via custom field values.
        Validates payload before sending to API.
        """
        validated_payload = CatalogAssetMetadataPayloadBuilder.build(custom_field_values)
        self._with_valid_token()
        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/integration/v2/custom_field_value/async/"
        try:
            response = requests.put(url, headers=headers, json=validated_payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._handle_request_error(e, "update_catalog_asset_metadata")

    def check_job_status(self, job_id: int) -> dict:
        """
        Check the status of a bulk metadata job in Alation by job ID.

        Args:
            job_id (int): The integer job identifier returned by a previous bulk operation.

        Returns:
            dict: The API response containing job status and details.
        """
        self._with_valid_token()

        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }
        params = {"id": job_id}
        url = f"{self.base_url}/api/v1/bulk_metadata/job/"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._handle_request_error(e, "check_job_status")

    def check_sql_query_tables(
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
        Check SQL query tables for data quality using the integration/v1/dq/check_sql_query_tables endpoint.
        Returns dict (JSON) or str (YAML Markdown) depending on output_format.
        """
        self._with_valid_token()
        headers = {
            "Token": self.access_token,
            "Accept": "application/json",
        }
        url = f"{self.base_url}/integration/v1/dq/check_sql_query_tables/"
        payload = {}
        if table_ids is not None:
            payload["table_ids"] = table_ids
        if sql_query is not None:
            payload["sql_query"] = sql_query
        if db_uri is not None:
            payload["db_uri"] = db_uri
        if ds_id is not None:
            payload["ds_id"] = ds_id

        if bypassed_dq_sources is not None:
            payload["bypassed_dq_sources"] = bypassed_dq_sources
        if default_schema_name is not None:
            payload["default_schema_name"] = default_schema_name
        if output_format is not None:
            payload["output_format"] = output_format
        if dq_score_threshold is not None:
            payload["dq_score_threshold"] = dq_score_threshold
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            if output_format and output_format.lower() == "yaml_markdown":
                return response.text
            return response.json()
        except requests.RequestException as e:
            self._handle_request_error(e, "check_sql_query_tables")
        except ValueError:
            raise AlationAPIError(
                message="Invalid JSON in data quality check response",
                status_code=None,
                response_body=None,
                reason="Malformed Response",
                resolution_hint="The server returned a non-JSON response. Contact support if this persists.",
                help_links=["https://developer.alation.com/"],
            )
