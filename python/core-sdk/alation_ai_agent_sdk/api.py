import logging
import time
import urllib.parse
import json
from typing import Dict, Any, Optional
from http import HTTPStatus
import requests
from datetime import datetime, timezone

# Constants for authentication methods
AUTH_METHOD_REFRESH_TOKEN = "refresh_token"
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
                "https://github.com/Alation/ai-agent-sdk/blob/main/guides/signature.md",
                "https://github.com/Alation/ai-agent-sdk/blob/main/README.md",
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
            help_links = ["https://developer.alation.com/"]
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
            reason = "Too Many Requests"
            resolution_hint = "Rate limit exceeded. Retry after some time."
            help_links = ["https://developer.alation.com/dev/docs/api-throttling"]
        elif status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            reason = "Internal Server Error"
            resolution_hint = "Server error. Retry later or contact Alation support."
            help_links = ["https://developer.alation.com/", "https://docs.alation.com/en/latest/"]

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


class AlationAPI:
    """
    Client for interacting with the Alation API.
    This class manages authentication (via refresh token or service account)
    and provides methods to retrieve context-specific information from the Alation catalog.

    Attributes:
    base_url (str): Base URL for the Alation instance
    user_id (int): Numeric ID of the Alation user
    refresh_token (str): Refresh token for API authentication
    access_token (str, optional): Current API access token
    client_id (str, optional): id from the OAuth Client Application
    client_secret (str, optional): secret from OAuth Client Application
    token_expiry (int): Timestamp for token expiration (Unix timestamp)
    """

    def __init__(
        self,
        base_url: str,
        user_id: Optional[int] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        self.access_token: Optional[str] = None
        self.token_expiry: float = 0  # Unix timestamp for token expiration

        if user_id is not None and refresh_token is not None:
            self.auth_method = AUTH_METHOD_REFRESH_TOKEN
            self.user_id = user_id
            self.refresh_token = refresh_token

        elif client_id is not None and client_secret is not None:
            self.auth_method = AUTH_METHOD_SERVICE_ACCOUNT
            self.client_id = client_id
            self.client_secret = client_secret

        else:
            raise ValueError(
                "Either (user_id and refresh_token) or (client_id and client_secret) must be provided."
            )
        logging.debug(f"AlationAPI initialized with auth method: {self.auth_method}")

    def _generate_access_token_with_refresh_token(self):
        """
        Generate a new access token using User ID and Refresh Token.
        """

        url = f"{self.base_url}/integration/v1/createAPIAccessToken/"
        payload = {
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
        }
        logging.debug(f"Generating access token using refresh token for user_id: {self.user_id}")

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
            response_text = getattr(e.response, "text", "No response received from server")
            parsed = {"error": response_text}
            meta = AlationErrorClassifier.classify_token_error(status_code, parsed)

            raise AlationAPIError(
                "HTTP error during access token generation",
                original_exception=e,
                status_code=status_code,
                response_body=parsed,
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

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

        expires_at_str = data["token_expires_at"]

        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )

        self.token_expiry = expires_at.timestamp()
        logging.debug(f"Access token generated from refresh token")

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
        logging.debug(f"Generating JWT token")
        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
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

        if "access_token" not in data or "expires_in" not in data:
            meta = AlationErrorClassifier.classify_token_error(response.status_code, data)
            raise AlationAPIError(
                f"Access token or expires_in missing in JWT API response from {url}",
                status_code=response.status_code,
                response_body=str(data),
                reason=meta.get("reason", "Malformed JWT Response"),
                resolution_hint=meta.get(
                    "resolution_hint", "Ensure client_id and client_secret are correct."
                ),
                help_links=meta["help_links"],
            )

        self.access_token = data["access_token"]
        expires_in_seconds = int(data["expires_in"])
        self.token_expiry = time.time() + expires_in_seconds
        logging.debug(f"JWT token generated from client ID and secret")

    def _ensure_token_is_valid(self):
        """
        Ensures a valid access token is available, generating one if needed.
        """
        if self.access_token is not None and time.time() < (self.token_expiry - 60):
            logging.debug("Access token is still valid.")
            return

        logging.info("Access token is invalid or expired. Attempting to generate a new one.")
        if self.auth_method == AUTH_METHOD_REFRESH_TOKEN:
            self._generate_access_token_with_refresh_token()
        elif self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            self._generate_jwt_token()
        else:
            raise AlationAPIError(
                "Invalid authentication method configured.",
                reason="Internal SDK Error",
                resolution_hint="SDK improperly configured.",
            )

    def get_context_from_catalog(self, query: str, signature: Optional[Dict[str, Any]] = None):
        """
        Retrieve contextual information from the Alation catalog based on a natural language query and signature.
        """
        if not query:
            raise ValueError("Query cannot be empty")

        self._ensure_token_is_valid()

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
        except requests.Timeout as e:
            raise AlationAPIError(
                "Request timed out while trying to fetch context",
                original_exception=e,
                status_code=HTTPStatus.REQUEST_TIMEOUT,
                response_body=None,
                reason="Context Request Timeout",
                resolution_hint="The server took too long to respond. Try again later.",
                help_links=["https://developer.alation.com/dev/docs/alation-api-overview"],
            )
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR)
            response_text = getattr(e.response, "text", "No response received from server")
            parsed = {"error": response_text}
            meta = AlationErrorClassifier.classify_catalog_error(status_code, parsed)

            raise AlationAPIError(
                "HTTP error during catalog search",
                original_exception=e,
                status_code=status_code,
                response_body=parsed,
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

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
