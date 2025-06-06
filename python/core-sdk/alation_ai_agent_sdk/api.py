import logging
import urllib.parse
import json
import re
from typing import Dict, Any, Optional, Union, NamedTuple
from http import HTTPStatus
import requests
import requests.exceptions

AUTH_METHOD_USER_ACCOUNT = "user_account"
AUTH_METHOD_SERVICE_ACCOUNT = "service_account"

logger = logging.getLogger(__name__)


class AlationAPIError(Exception):
    """Raised when an Alation API call fails logically or at HTTP level."""

    def __init__(
        self,
        message: str,
        *,
        original_exception=None,
        status_code=None,
        response_body=None,
        reason=None,
        resolution_hint=None,
        help_links=None,
    ):
        super().__init__(message)
        self.original_exception = original_exception
        self.status_code = status_code
        self.response_body = response_body
        self.reason = reason
        self.resolution_hint = resolution_hint
        self.help_links = help_links or []

    def to_dict(self) -> dict:
        return {
            "message": str(self),
            "status_code": self.status_code,
            "reason": self.reason,
            "resolution_hint": self.resolution_hint,
            "is_retryable": self.status_code
            in [
                HTTPStatus.TOO_MANY_REQUESTS,
                HTTPStatus.INTERNAL_SERVER_ERROR,
            ],
            "response_body": self.response_body,
            "help_links": self.help_links,
        }


class AlationErrorClassifier:
    @staticmethod
    def classify_catalog_error(status_code: int, response_body: dict) -> Dict[str, Any]:
        reason = "Unexpected Error"
        resolution_hint = "An unknown error occurred."
        help_links = []

        if status_code == HTTPStatus.BAD_REQUEST:
            reason = "Bad Request"
            resolution_hint = (
                response_body.get("error")
                or response_body.get("message")
                or "Request was malformed. Check the query and signature structure."
            )
            help_links = [
                "https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/signature.md",
                "https://github.com/Alation/alation-ai-agent-sdk?tab=readme-ov-file#usage",
                "https://developer.alation.com/dev/docs/customize-the-aggregated-context-api-calls-with-a-signature",
            ]
        elif status_code == HTTPStatus.UNAUTHORIZED:
            reason = "Unauthorized"
            resolution_hint = "Token missing or invalid. Retry with a valid token."
            help_links = [
                "https://developer.alation.com/dev/v2024.1/docs/authentication-into-alation-apis",
                "https://developer.alation.com/dev/reference/refresh-access-token-overview",
            ]
        elif status_code == HTTPStatus.FORBIDDEN:
            reason = "Forbidden"
            resolution_hint = (
                "Token likely expired or lacks permissions. Ask the user to re-authenticate."
            )
            help_links = [
                "https://developer.alation.com/dev/v2024.1/docs/authentication-into-alation-apis",
                "https://developer.alation.com/dev/reference/refresh-access-token-overview",
            ]
        elif status_code == HTTPStatus.NOT_FOUND:
            reason = "Not Found"
            resolution_hint = (
                "The requested resource was not found or is not enabled, check feature flag"
            )
            help_links = [
                "https://developer.alation.com/dev/docs/guide-to-aggregated-context-api-beta"
            ]
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
            reason = "Too Many Requests"
            resolution_hint = "Rate limit exceeded. Retry after some time."
            help_links = [
                "https://developer.alation.com/dev/docs/guide-to-aggregated-context-api-beta#rate-limiting"
            ]
        elif status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            reason = "Internal Server Error"
            resolution_hint = "Server error. Retry later or contact Alation support."
            help_links = [
                "https://developer.alation.com/dev/docs/guide-to-aggregated-context-api-beta"
            ]

        return {"reason": reason, "resolution_hint": resolution_hint, "help_links": help_links}

    @staticmethod
    def classify_token_error(status_code: int, response_body: dict) -> Dict[str, Any]:
        reason = "Unexpected Token Error"
        resolution_hint = "An unknown token-related error occurred."
        help_links = [
            "https://developer.alation.com/dev/v2024.1/docs/authentication-into-alation-apis",
            "https://developer.alation.com/dev/reference/refresh-access-token-overview",
        ]

        if status_code == HTTPStatus.BAD_REQUEST:
            reason = "Token Request Invalid"
            resolution_hint = response_body.get("error") or "Token request payload is malformed."
        elif status_code == HTTPStatus.UNAUTHORIZED:
            reason = "Token Unauthorized"
            resolution_hint = "[User ID,refresh token] or [client id, client secret] is invalid."
        elif status_code == HTTPStatus.FORBIDDEN:
            reason = "Token Forbidden"
            resolution_hint = "You do not have permission to generate a token."
        elif status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            reason = "Token Generation Failed"
            resolution_hint = "Alation server failed to process token request."

        return {"reason": reason, "resolution_hint": resolution_hint, "help_links": help_links}


class UserAccountAuthParams(NamedTuple):
    user_id: int
    refresh_token: str


class ServiceAccountAuthParams(NamedTuple):
    client_id: str
    client_secret: str


AuthParams = Union[UserAccountAuthParams, ServiceAccountAuthParams]


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
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.auth_method = auth_method

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

    def _handle_request_error(self, exception: requests.RequestException, context: str):
        """Utility function to handle request exceptions."""
        if isinstance(exception, requests.exceptions.Timeout):
            raise AlationAPIError(
                f"Request to {context} timed out after 60 seconds.",
                reason="Timeout Error",
                resolution_hint="Ensure the server is reachable and try again later.",
                help_links=["https://developer.alation.com/"],
            )

        status_code = getattr(exception.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
        response_text = getattr(exception.response, "text", "No response received from server")
        parsed = {"error": response_text}
        meta = AlationErrorClassifier.classify_token_error(status_code, parsed)

        raise AlationAPIError(
            f"HTTP error during {context}",
            original_exception=exception,
            status_code=status_code,
            response_body=parsed,
            reason=meta["reason"],
            resolution_hint=meta["resolution_hint"],
            help_links=meta["help_links"],
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
        logger.debug(f"Access token generated from refresh token")

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
        logger.debug(f"Generating JWT token")
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
        logger.debug(f"JWT token generated from client ID and secret")

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

        params = {"question": query}
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
