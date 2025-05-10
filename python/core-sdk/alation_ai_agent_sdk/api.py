import logging
import time
import urllib.parse
import json
from typing import Dict, Any, Optional
from http import HTTPStatus
import requests


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
            # TODO: add link to doc explaining how to enable this API
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
            resolution_hint = "User ID or refresh token is invalid."
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
    This class manages authentication and provides methods to retrieve
    context-specific information from the Alation catalog.
    Attributes:
        base_url (str): Base URL for the Alation instance
        user_id (int): Numeric ID of the Alation user
        refresh_token (str): Refresh token for API authentication
        access_token (str, optional): Current API access token
        token_expiry (int): Timestamp for token expiration (Unix timestamp)
    """

    def __init__(self, base_url: str, user_id: int, refresh_token: str):
        self.base_url = base_url
        self.user_id = user_id
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expiry = 0

    def _is_token_valid(self) -> bool:
        """
        Check if the current token is still valid with a safety buffer.
        Returns:
            bool: True if the token is valid, False otherwise
        """
        return self.access_token is not None and time.time() < self.token_expiry

    def _generate_access_token(self):
        """
        Generate a new access token for API authentication.
        """

        # Skip token generation if the current token is still valid
        if self._is_token_valid():
            return

        url = f"{self.base_url}/integration/v1/createAPIAccessToken/"
        payload = {
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
        except requests.Timeout as e:
            raise AlationAPIError(
                "Request timed out while trying to generate access token",
                original_exception=e,
                status_code=HTTPStatus.REQUEST_TIMEOUT,
                response_body=None,
                reason="Token Request Timeout",
                resolution_hint="The server took too long to respond. Try again in a few seconds.",
                help_links=[
                    "https://developer.alation.com/dev/v2024.1/docs/authentication-into-alation-apis"
                ],
            )
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

        if data.get("status") == "failed":
            logging.error("Access token generation logical failure: %s", data)
            meta = AlationErrorClassifier.classify_token_error(response.status_code, data)
            raise AlationAPIError(
                "Logical failure in access token generation",
                status_code=response.status_code,
                response_body=str(data),
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

        try:
            self.access_token = data["api_access_token"]
        except KeyError:
            meta = AlationErrorClassifier.classify_token_error(response.status_code, data)
            raise AlationAPIError(
                "Access token missing in API response",
                status_code=response.status_code,
                response_body=str(data),
                reason=meta["reason"],
                resolution_hint=meta["resolution_hint"],
                help_links=meta["help_links"],
            )

        self.token_expiry = time.time() + 24 * 60 * 60

    def get_context_from_catalog(self, query: str, signature: Optional[Dict[str, Any]] = None):
        """
        Retrieve contextual information from the Alation catalog based on a natural language query and signature.
        """
        if not query:
            raise ValueError("Query cannot be empty")

        self._generate_access_token()

        headers = {
            "Token": self.access_token,
        }

        params = {"question": query}
        # If a signature is provided, include it in the request
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
