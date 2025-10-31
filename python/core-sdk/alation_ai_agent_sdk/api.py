import time
import logging
import urllib.parse
import json
import requests
import requests.exceptions
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from http import HTTPStatus
from uuid import uuid4
from alation_ai_agent_sdk.lineage_filtering import filter_graph
from .types import (
    ServiceAccountAuthParams,
    BearerTokenAuthParams,
    SessionAuthParams,
    AuthParams,
    CatalogAssetMetadataPayloadItem,
)
from .utils import SDK_VERSION
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

AUTH_METHOD_SERVICE_ACCOUNT = "service_account"
AUTH_METHOD_BEARER_TOKEN = "bearer_token"
AUTH_METHOD_SESSION = "session"

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
            raise ValueError(
                f"Invalid otype: {obj['otype']}. Allowed: {cls.ALLOWED_OTYPES}"
            )
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


DEFAULT_CONNECT_TIMEOUT_IN_SECONDS = 60
DEFAULT_READ_TIMEOUT_IN_SECONDS = 300


class AlationAPI:
    """
    Client for interacting with the Alation API.
    This class manages authentication (via refresh token, service account, bearer token, or session cookie)
    and provides methods to retrieve context-specific information from the Alation catalog.

    Attributes:
        base_url (str): Base URL for the Alation instance
        auth_method (str): Authentication method ("service_account", "bearer_token", or "session")
        auth_params (AuthParams): Parameters required for the chosen authentication method
    """

    def __init__(
        self,
        base_url: str,
        auth_method: str,
        auth_params: AuthParams,
        dist_version: Optional[str] = None,
        skip_instance_info: Optional[bool] = False,
        enable_streaming: Optional[bool] = False,
        decode_nested_json: Optional[bool] = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.auth_method = auth_method
        self.enable_streaming = enable_streaming
        self.decode_nested_json = decode_nested_json
        self.is_cloud = None
        self.alation_release_name = None
        self.alation_version_info = None
        self.dist_version = dist_version

        # Validate auth_method and auth_params
        if auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            if not isinstance(auth_params, ServiceAccountAuthParams):
                raise ValueError(
                    "For 'service_account' authentication, provide a tuple with (client_id: str, client_secret: str)."
                )
            self.client_id, self.client_secret = auth_params
        elif auth_method == AUTH_METHOD_BEARER_TOKEN:
            if not isinstance(auth_params, BearerTokenAuthParams):
                raise ValueError(
                    "For 'bearer_token' authentication, provide a tuple with (token: str)."
                )
            self.access_token = auth_params.token
        elif auth_method == AUTH_METHOD_SESSION:
            if not isinstance(auth_params, SessionAuthParams):
                raise ValueError(
                    "For 'session' authentication, provide a tuple with (session_cookie: str)."
                )
            self.session_cookie = auth_params.session_cookie
        else:
            raise ValueError(
                "auth_method must be 'service_account', 'bearer_token', or 'session'."
            )

        logger.debug(f"AlationAPI initialized with auth method: {self.auth_method}")

        if not skip_instance_info:
            self._fetch_and_cache_instance_info()

    def _fetch_and_cache_instance_info(self):
        """
        Fetches instance info (license and version) after authentication and caches in memory.
        """
        self._with_valid_auth()
        headers = self._get_request_headers()
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

    def _handle_request_error(
        self, exception: requests.RequestException, context: str, timeout=None
    ):
        """Utility function to handle request exceptions."""

        alation_release_name = getattr(self, "alation_release_name", None)
        dist_version = getattr(self, "dist_version", None)

        if isinstance(exception, requests.exceptions.Timeout):
            if timeout is None:
                timeout = DEFAULT_READ_TIMEOUT_IN_SECONDS
            raise AlationAPIError(
                f"Request to {context} timed out after {timeout} seconds.",
                reason="Timeout Error",
                resolution_hint="Ensure the server is reachable and try again later.",
                help_links=["https://developer.alation.com/"],
                alation_release_name=alation_release_name,
                dist_version=dist_version,
            )
        if isinstance(exception, requests.exceptions.ReadTimeout):
            raise AlationAPIError(
                f"Read operation timed out during {context} after {timeout} seconds.",
                reason="Read Timeout",
                resolution_hint="The server took too long to send the next message. Try again later.",
                help_links=["https://developer.alation.com/"],
                alation_release_name=alation_release_name,
                dist_version=dist_version,
            )

        status_code = getattr(
            exception.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR
        )
        response_text = getattr(
            exception.response, "text", "No response received from server"
        )
        if exception.response is not None:
            try:
                parsed = exception.response.json()
            except (json.JSONDecodeError, ValueError):
                parsed = {"error": response_text}
        else:
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
            is_retryable=meta.get("is_retryable"),
        )

    def _get_response_meta(self, response: requests.Response) -> Dict[str, Any] | None:
        """
        Extract meta information from the response headers.

        Returns:
            Dict[str, Any]: A dictionary containing meta information from the response headers.
        """
        meta = None
        if "X-Entitlement-Warning" in getattr(response, "headers", {}):
            meta = {
                "X-Entitlement-Limit": response.headers.get("X-Entitlement-Limit"),
                "X-Entitlement-Usage": response.headers.get("X-Entitlement-Usage"),
                "X-Entitlement-Warning": response.headers["X-Entitlement-Warning"],
            }
        return meta

    def _format_successful_response(
        self, response: requests.Response
    ) -> Union[Dict[str, Any], str]:
        """
        Format a successful response from the Alation API.
        Returns:
            Union[Dict[str, Any], str]: The formatted response data with entitlement info injected
        """
        if not (200 <= response.status_code < 300):
            return response.json()

        data = response.json()

        meta = self._get_response_meta(response)
        # Check for entitlement headers and inject meta information if present
        if meta:
            # Maintain backward compatibility by injecting meta into the existing response structure
            if isinstance(data, dict):
                # If response is a dict, add _meta field (underscore prefix to avoid conflicts)
                data["_meta"] = {"headers": meta}
            elif isinstance(data, list):
                # If response is a list, wrap it to include meta information
                data = {"results": data, "_meta": {"headers": meta}}

        return data

    def _generate_access_token_with_refresh_token(self):
        """
        Generate a new access token using User ID and Refresh Token.
        """

        url = f"{self.base_url}/integration/v1/createAPIAccessToken/"
        payload = {
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
        }
        logger.debug(
            f"Generating access token using refresh token for user_id: {self.user_id}"
        )

        try:
            response = requests.post(
                url, json=payload, timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self._handle_request_error(
                e, "access token generation", timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
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
            meta = AlationErrorClassifier.classify_token_error(
                response.status_code, data
            )
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
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self._handle_request_error(
                e, "JWT token generation", timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
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

        if "access_token" not in data:
            meta = AlationErrorClassifier.classify_token_error(
                response.status_code, data
            )
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
        logger.info(
            "Access token is invalid or expired. Attempting to generate a new one."
        )
        if self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
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
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            status_code = getattr(
                e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR
            )

            if status_code is HTTPStatus.UNAUTHORIZED:
                return False

            response_text = getattr(
                e.response, "text", "No response received from server"
            )
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
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("active", False)
        except requests.RequestException as e:
            status_code = getattr(
                e.response, "status_code", HTTPStatus.INTERNAL_SERVER_ERROR
            )
            response_text = getattr(
                e.response, "text", "No response received from server"
            )
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
            if self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
                return self._is_jwt_token_valid()
        except Exception as e:
            logger.error(f"Error validating token on server: {e}")
            return False

    def _with_valid_auth(self, disallowed_methods: Optional[List[str]] = None):
        """
        Ensures authentication is ready for API calls.

        For token-based auth (user_account, service_account): validates and refreshes tokens as needed.
        For credential-based auth (bearer_token, session): assumes credentials are valid (validation happens at request time).
        """

        # Certain API endpoints may only support specific auth methods
        if disallowed_methods is not None and self.auth_method in disallowed_methods:
            raise AlationAPIError(
                f"Authentication method '{self.auth_method}' is not allowed for this operation.",
                reason="Invalid Authentication Method",
                resolution_hint="Use an alternative authorization method.",
            )

        if self.auth_method in (AUTH_METHOD_BEARER_TOKEN, AUTH_METHOD_SESSION):
            # For bearer tokens and session cookies, we assume they are valid
            # Validation happens at the API request level
            return

        # For token-based authentication, check validity and refresh if needed
        try:
            if self.access_token and self._token_is_valid_on_server():
                logger.debug("Access token is valid on server")
                return
        except Exception as e:
            logger.error(f"Error checking token validity: {e}")

        self._generate_new_token()

    def _get_request_headers(
        self, header_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get the appropriate request headers including authentication based on the auth method.

        Returns:
            Dict[str, str]: Headers dictionary with authentication and content type information
        """
        headers = {"Accept": "application/json"}

        # Set User-Agent header to be dist_version/sdk_version if either is present
        user_agent = f"{self.dist_version}/" if self.dist_version else ""
        if SDK_VERSION:
            user_agent += f"sdk-{SDK_VERSION}"
        if user_agent:
            headers["User-Agent"] = user_agent

        if self.auth_method == AUTH_METHOD_SESSION:
            headers["Cookie"] = self.session_cookie
        elif self.access_token:
            headers["Token"] = self.access_token

        if header_overrides:
            headers.update(header_overrides)

        return headers

    def _get_streaming_request_headers(self) -> Dict[str, str]:
        """
        Get the appropriate request headers for streaming requests including authentication based on the auth method.

        Returns:
            Dict[str, str]: Headers dictionary with authentication and content type information
        """
        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }
        if (
            self.auth_method == AUTH_METHOD_BEARER_TOKEN
            or self.auth_method == AUTH_METHOD_SERVICE_ACCOUNT
        ):
            headers["Authorization"] = f"Bearer {self.access_token}"
        return self._get_request_headers(header_overrides=headers)

    def _get_streaming_timeouts(
        self,
        connect_timeout: Optional[Union[float, int]] = None,
        read_timeout: Optional[Union[float, int]] = None,
    ) -> Tuple[Union[float, int], Union[float, int]]:
        """
        Get the appropriate timeouts for streaming requests.

        Args:
            connect_timeout (float|int, optional): Connection timeout in seconds. Defaults to 10 seconds.
            read_timeout (float|int, optional): Read timeout in seconds. Defaults to 300 seconds.

        Returns:
            Tuple[Union[float, int], Union[float, int]]: A tuple containing the connect and read timeouts.
        """
        return (
            connect_timeout
            if connect_timeout is not None
            else DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            read_timeout
            if read_timeout is not None
            else DEFAULT_READ_TIMEOUT_IN_SECONDS,
        )

    def _is_likely_json_value(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        if value.startswith("{") and value.endswith("}"):
            return True
        if value.startswith("[") and value.endswith("]"):
            return True
        return False

    def _decode_json_string(self, value: Any) -> Any:
        """Attempt to JSON-decode a string value if it appears to be JSON.

        Returns the decoded python object on success, otherwise returns the original value.
        """
        if not self._is_likely_json_value(value):
            return value
        try:
            return json.loads(value)  # type: ignore[arg-type]
        except (json.JSONDecodeError, TypeError):
            return value

    def _shallow_decode_collection(self, obj: Any) -> Any:
        """Decode any immediate JSON-encoded string members in a dict or list.

        This mirrors the original behavior which performed a single extra decoding
        pass on children (i.e. it is intentionally not fully recursive).
        """
        if isinstance(obj, dict):
            decoded: Dict[str, Any] = {}
            for k, v in obj.items():
                decoded[k] = self._decode_json_string(v)
            return decoded
        if isinstance(obj, list):
            return [self._decode_json_string(item) for item in obj]
        return obj

    def _decode_text_part_content(self, part: Dict[str, Any]) -> Any:
        """Decode the JSON contained in a text part's `content` field if present.

        If the `content` is a JSON string we decode it. If the decoded value is a
        list or dict we perform a single shallow pass attempting to decode any
        JSON-looking string children. On failure we return the original part.

        Return value:
            - Decoded object (dict | list | primitive) if decoding occurred
            - Original part dict if no decoding happened or an error occurred
        """
        if part.get("part_kind") != "text":
            return part
        content = part.get("content")
        if not isinstance(content, str):
            return part
        decoded_root = self._decode_json_string(content)
        # If decoding did not change the value, keep original part
        if decoded_root is content:
            return part
        # Perform one shallow decode pass for children if collection
        if isinstance(decoded_root, (dict, list)):
            decoded_root = self._shallow_decode_collection(decoded_root)
        return decoded_root

    def _decode_nested_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inline replacement of JSON-encoded values nested in model_message parts.

        For each part inside `data['model_message']['parts']` where
        `part_kind == 'text'`, if the part's `content` is a JSON string we:
            1. Decode the JSON string.
            2. If the decoded result is a dict or list, attempt a single shallow
               decode of its immediate children that also look like JSON strings.
            3. Replace the entire part object in the parts list with the decoded
               python object (maintaining original behavior of the previous implementation).

        Non-text parts and parts whose content is not valid JSON are left untouched.
        Any JSON decoding errors result in leaving the original part unchanged.
        """
        model_message = data.get("model_message")
        if not isinstance(model_message, dict):
            return data
        parts = model_message.get("parts")
        if not isinstance(parts, list):
            return data
        new_parts: List[Any] = []
        for part in parts:
            if not isinstance(part, dict):
                # Skip non-dict entries silently (mirrors original behavior of continue)
                continue
            decoded = self._decode_text_part_content(part)
            new_parts.append(decoded)
        model_message["parts"] = new_parts
        return data

    def _iter_sse_response(
        self, response: requests.Response, log_raw_stream_events: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data:"):
                if log_raw_stream_events:
                    logger.info(f"SSE Event: {decoded_line}")
                json_data_str = decoded_line[len("data:") :].strip()
                try:
                    event_data = json.loads(json_data_str)
                    if self.decode_nested_json:
                        event_data = self._decode_nested_json(event_data)
                    # Process the parsed JSON event data
                    yield event_data
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON: {e} in line: {json_data_str}")
                    continue

    def _sse_stream_or_last_event(
        self,
        response: requests.Response,
        log_raw_stream_events: bool = False,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generator to yield events from a Server-Sent Events (SSE) response.

        Args:
            response (requests.Response): The HTTP response object from the SSE endpoint.
            enable_streaming (bool): Flag to enable streaming mode.

        Yields:
            Dict[str, Any]: Parsed JSON data from each SSE event.
        """
        if self.enable_streaming:
            # Streaming mode, yield events as they arrive
            yield from self._iter_sse_response(response, log_raw_stream_events=log_raw_stream_events)
        else:
            # Non-streaming mode: collect all events and yield once.
            # WARNING: There are an awful lot of tokens returned here that aren't particularly applicable.
            # TBD: Maybe clean these up to only return the payload instead of the whole message etc.
            last_event = None
            for event in self._iter_sse_response(response, log_raw_stream_events=log_raw_stream_events):
                last_event = event
            yield last_event

    def _safe_sse_post_request(
        self,
        tool_name: str,
        url: str,
        payload: Dict[str, Any],
        timeouts: Optional[Tuple[Union[float, int], Union[float, int]]] = None,
        log_raw_stream_events: bool = False,
    ) -> Generator[Dict[str, Any], None, None]:
        self._with_valid_auth(disallowed_methods=["user_account", AUTH_METHOD_SESSION])

        headers = self._get_streaming_request_headers()
        if timeouts is None:
            timeouts = self._get_streaming_timeouts()
        try:
            with requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=timeouts,
            ) as response:
                response_meta = self._get_response_meta(response)
                if response_meta:
                    # NOTE: We shifted from user seeing warnings to logging them as warnings
                    logger.warning(
                        f"At or nearing usage limits: {json.dumps(response_meta)}"
                    )
                yield from self._sse_stream_or_last_event(response, log_raw_stream_events=log_raw_stream_events)
        except requests.exceptions.ReadTimeout as e:
            logger.error(f"Read timed out while using {tool_name}: {e}")
            self._handle_request_error(
                e, f"{tool_name} - read timeout", timeout=timeouts[1]
            )
        except requests.exceptions.ConnectTimeout as e:
            logger.error(f"Connection timed out while using {tool_name}: {e}")
            self._handle_request_error(
                e, f"{tool_name} - connection timeout", timeout=timeouts[0]
            )
        except requests.RequestException as e:
            logger.error(f"Error occurred while using {tool_name}: {e}")
            self._handle_request_error(e, f"{tool_name} - general error", timeout=0)

    def get_context_from_catalog(
        self, query: str, signature: Optional[Dict[str, Any]] = None
    ):
        """
        Retrieve contextual information from the Alation catalog based on a natural language query and signature.
        """
        if not query:
            raise ValueError("Query cannot be empty")

        self._with_valid_auth()

        headers = self._get_request_headers()

        params = {"question": query, "mode": "search"}
        if signature:
            params["signature"] = json.dumps(signature, separators=(",", ":"))

        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{self.base_url}/integration/v2/context/?{encoded_params}"

        try:
            response = requests.get(
                url, headers=headers, timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )
            response.raise_for_status()

        except requests.RequestException as e:
            self._handle_request_error(
                e, "catalog search", timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )

        try:
            return self._format_successful_response(response)
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
        self._with_valid_auth()
        headers = self._get_request_headers()

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
                self._handle_request_error(
                    e, f"fetching data product by id: {product_id}"
                )

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
                if response_data and (data_products := response_data.get("results", [])):
                    instructions = (
                        f"Found {len(data_products)} data product{'s' if len(data_products) > 1 else ''} matching your query. "
                        "The following contains summary information (name, id, description, url) for each product. "
                        "To get complete specifications, call this tool again with a specific product_id."
                    )
                    results = [
                        {
                            "id": product["product"]["product_id"],
                            "name": product["product"]["spec_json"]["product"]["en"][
                                "name"
                            ],
                            "description": product["product"]["spec_json"]["product"][
                                "en"
                            ]["description"],
                            "url": f"{self.base_url}/app/marketplace/{self.marketplace_id}/data-product/{product['product']['product_id']}/",
                        }
                        for product in data_products
                    ]
                    return {"instructions": instructions, "results": results}
                return {
                    "instructions": "No data products found for the given query.",
                    "results": [],
                }
            except requests.RequestException as e:
                self._handle_request_error(
                    e, f"searching data products with query: {query}"
                )

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
                raise ValueError(
                    "allowed_otypes is only supported in 'complete' processing mode."
                )
            if len(allowed_otypes) == 0:
                raise ValueError("allowed_otypes cannot be empty list.")
        if (
            pagination is not None
            and processing_mode == LineageGraphProcessingOptions.COMPLETE
        ):
            raise ValueError(
                "pagination is only supported in 'chunked' processing mode."
            )

        self._with_valid_auth()

        headers = self._get_request_headers()

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
                else pagination.get("batch_size", limit)
                if pagination
                else batch_size
            ),
        }
        if show_temporal_objects:
            lineage_request_dict["filters"]["temp_filter"] = show_temporal_objects
        url = f"{self.base_url}/integration/v2/bulk_lineage/"
        try:
            response = requests.post(
                url,
                headers=headers,
                json=lineage_request_dict,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
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
                e,
                f"getting lineage for: {json.dumps(lineage_request_dict)}",
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )

    def update_catalog_asset_metadata(
        self, custom_field_values: list[CatalogAssetMetadataPayloadItem]
    ) -> dict:
        """
        Updates metadata for one or more Alation catalog assets via custom field values.
        Validates payload before sending to API.
        """
        validated_payload = CatalogAssetMetadataPayloadBuilder.build(
            custom_field_values
        )
        self._with_valid_auth()
        headers = self._get_request_headers()
        headers["Content-Type"] = "application/json"
        url = f"{self.base_url}/integration/v2/custom_field_value/async/"
        try:
            response = requests.put(
                url,
                headers=headers,
                json=validated_payload,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self._handle_request_error(
                e,
                "update_catalog_asset_metadata",
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )

    def check_job_status(self, job_id: int) -> dict:
        """
        Check the status of a bulk metadata job in Alation by job ID.

        Args:
            job_id (int): The integer job identifier returned by a previous bulk operation.

        Returns:
            dict: The API response containing job status and details.
        """
        # Session auth is not supported for this endpoint (internal restriction)
        if self.auth_method == AUTH_METHOD_SESSION:
            raise AlationAPIError(
                "Session authentication is not supported for check_job_status",
                reason="Unsupported Authentication Method",
                resolution_hint="Use user_account, service_account, or bearer_token authentication instead",
                help_links=["https://developer.alation.com/"],
            )

        self._with_valid_auth()

        headers = self._get_request_headers()
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
        self._with_valid_auth()
        headers = self._get_request_headers()
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
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
            )
            response.raise_for_status()
            if output_format and output_format.lower() == "yaml_markdown":
                return response.text
            return response.json()
        except requests.RequestException as e:
            self._handle_request_error(
                e, "check_sql_query_tables", timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )
        except ValueError:
            raise AlationAPIError(
                message="Invalid JSON in data quality check response",
                status_code=None,
                response_body=None,
                reason="Malformed Response",
                resolution_hint="The server returned a non-JSON response. Contact support if this persists.",
                help_links=["https://developer.alation.com/"],
            )

    def get_custom_fields(self) -> List[Dict[str, Any]]:
        """
        Retrieve all custom field definitions from the Alation instance.

        Requires Catalog or Server admin permissions.

        Returns:
            List[Dict[str, Any]]: List of custom field objects

        Raises:
            AlationAPIError: On network, API, authentication, or authorization errors
        """
        self._with_valid_auth()

        headers = self._get_request_headers()

        url = f"{self.base_url}/integration/v2/custom_field/"

        try:
            response = requests.get(
                url, headers=headers, timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            self._handle_request_error(
                e, "custom fields retrieval", timeout=DEFAULT_CONNECT_TIMEOUT_IN_SECONDS
            )

    def alation_context_stream(
        self,
        question: str,
        signature: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieve contextual information from the Alation catalog using alation_context_tool.
        """
        payload = {"question": question}
        if signature is not None:
            payload["signature"] = signature
        url = (
            f"{self.base_url}/ai/api/v1/chats/tool/default/alation_context_tool/stream"
        )
        if chat_id is not None:
            url += f"?chat_id={chat_id}"

        yield from self._safe_sse_post_request(
            tool_name="alation_context",
            url=url,
            payload=payload,
            timeouts=None,
        )

    def analyze_catalog_question_stream(
        self,
        question: str,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Analyze catalog questions and return workflow guidance.
        """
        url = f"{self.base_url}/ai/api/v1/chats/tool/default/analyze_catalog_question_tool/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="analyze_catalog_question",
            url=url,
            payload={"question": question},
            timeouts=None,
        )

    def bulk_retrieval_stream(
        self,
        signature: Dict[str, Any],
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieve bulk objects from the Alation catalog using bulk_retrieval_tool.
        """
        url = f"{self.base_url}/ai/api/v1/chats/tool/default/bulk_retrieval_tool/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="bulk_retrieval",
            url=url,
            payload={"signature": signature},
            timeouts=None,
        )

    def get_custom_field_definitions_stream(
        self,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieve all custom field definitions from the Alation instance.
        """
        url = f"{self.base_url}/ai/api/v1/chats/tool/default/get_custom_fields_definitions_tool/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="get_custom_field_definitions",
            url=url,
            payload={},
            timeouts=None,
        )

    def get_signature_creation_instructions_stream(
        self, chat_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns comprehensive instructions for creating the signature parameter.
        """
        url = f"{self.base_url}/ai/api/v1/chats/tool/default/get_signature_creation_instructions_tool/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="get_signature_creation_instructions",
            url=url,
            payload={},
            timeouts=None,
        )

    def catalog_context_search_agent_stream(
        self,
        message: str,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Catalog Context Search Agent for searching catalog objects with context.
        """
        url = f"{self.base_url}/ai/api/v1/chats/agent/default/catalog_context_search_agent/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="catalog_context_search_agent",
            url=url,
            payload={"message": message},
            timeouts=None,
        )

    def query_flow_agent_stream(
        self,
        message: str,
        marketplace_id: str,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Query Flow Agent for SQL query workflow management.
        """
        url = f"{self.base_url}/ai/api/v1/chats/agent/default/query_flow_agent/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="query_flow_agent",
            url=url,
            payload={"message": message, "marketplace_id": marketplace_id},
            timeouts=None,
        )

    def sql_query_agent_stream(
        self,
        message: str,
        data_product_id: str,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        SQL Query Agent for SQL query generation and analysis.
        """
        url = f"{self.base_url}/ai/api/v1/chats/agent/default/sql_query_agent/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="sql_query_agent",
            url=url,
            payload={"message": message, "data_product_id": data_product_id},
            timeouts=None,
        )

    def get_data_sources_tool_stream(
        self,
        limit: int = 100,
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieve available data sources from the catalog.
        """
        payload = {"limit": limit}

        url = (
            f"{self.base_url}/ai/api/v1/chats/tool/default/get_data_sources_tool/stream"
        )
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="get_data_sources_tool",
            url=url,
            payload=payload,
            timeouts=None,
        )

    def custom_agent_stream(
        self,
        agent_config_id: str,
        payload: Dict[str, Any],
        chat_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream responses from a custom agent.
        """
        url = f"{self.base_url}/ai/api/v1/chats/agent/{agent_config_id}/stream"
        if chat_id is not None:
            url += f"?chat_id={chat_id}"
        yield from self._safe_sse_post_request(
            tool_name="custom_agent_stream",
            url=url,
            payload=payload,
            timeouts=None,
        )

    def post_tool_event(
        self,
        event: dict,
        timeout: float,
        max_retries: int,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Post a tool event to the Alation API.
        Args:
            event (dict): The tool event to post.
            timeout (float): The timeout for the request.
            max_retries (int): The maximum number of retry attempts.
            extra_headers (Optional[Dict[str, str]]): Additional headers to include in the request.
        """
        self._with_valid_auth()

        headers = self._get_request_headers()
        headers.update(extra_headers or {})

        url = f"{self.base_url}/api/v1/ai_agent/tool/event/"

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url, headers=headers, json=event, timeout=timeout
                )
                response.raise_for_status()
                logger.debug(
                    f"Event sent successfully: {event.get('tool_name', 'unknown')}"
                )
                return
            except requests.RequestException as e:
                try:
                    self._handle_request_error(e, "post tool event")
                except AlationAPIError as api_error:
                    if attempt == max_retries or not getattr(
                        api_error, "is_retryable", False
                    ):
                        logger.warning(
                            f"Max retries reached for event tracking: {event.get('tool_name', 'unknown')}"
                        )
                        raise
                    else:
                        logger.warning(
                            f"Retrying event tracking: {event.get('tool_name', 'unknown')} (Attempt {attempt + 1}/{max_retries + 1})"
                        )
                        time.sleep(0.1 * (2**attempt))  # Exponential backoff
