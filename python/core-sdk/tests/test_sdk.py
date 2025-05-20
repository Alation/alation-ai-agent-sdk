import pytest
import requests
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from alation_ai_agent_sdk.sdk import AlationAIAgentSDK
from alation_ai_agent_sdk.api import (
    AUTH_METHOD_REFRESH_TOKEN,
    AUTH_METHOD_SERVICE_ACCOUNT,
)


# --- Mock API Responses & Constants ---
MOCK_BASE_URL = "https://fake-alation-instance.com"
MOCK_USER_ID = 123
MOCK_REFRESH_TOKEN = "test-refresh-token"
MOCK_CLIENT_ID = "test-client-id"
MOCK_CLIENT_SECRET = "test-client-secret"

REFRESH_TOKEN_EXPIRES_AT = (
    (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace("+00:00", "Z")
)

REFRESH_TOKEN_RESPONSE_SUCCESS = {
    "api_access_token": "mock-api-access-token-from-refresh",
    "status": "success",
    "user_id": MOCK_USER_ID,
    "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "token_expires_at": REFRESH_TOKEN_EXPIRES_AT,
    "token_status": "ACTIVE",
}

JWT_RESPONSE_SUCCESS = {
    "access_token": "mock-jwt-access-token",
    "expires_in": 3600,
    "token_type": "Bearer",
}

CONTEXT_RESPONSE_SUCCESS = {"some_context_key": "some_context_value"}


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mocks requests.post with a flexible router for different URLs."""
    mock_post_responses = {}

    def _add_mock_response(
        url_identifier,
        response_json=None,
        status_code=200,
        raise_for_status_exception=None,
        side_effect=None,
    ):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = status_code
        if response_json is not None:
            mock_response.json = MagicMock(return_value=response_json)
        else:
            mock_response.json = MagicMock(
                side_effect=requests.exceptions.JSONDecodeError("No JSON", "doc", 0)
            )

        if raise_for_status_exception:
            mock_response.raise_for_status = MagicMock(side_effect=raise_for_status_exception)
        else:
            mock_response.raise_for_status = MagicMock()

        if side_effect:
            mock_post_responses[url_identifier] = MagicMock(side_effect=side_effect)
        else:
            mock_post_responses[url_identifier] = MagicMock(return_value=mock_response)

    def mock_post_router(*args, **kwargs):
        url = args[0]

        if "createAPIAccessToken" in url:
            if "createAPIAccessToken" in mock_post_responses:
                return mock_post_responses["createAPIAccessToken"](*args, **kwargs)
        elif "auth/accessToken" in url:
            if "auth/accessToken" in mock_post_responses:
                return mock_post_responses["auth/accessToken"](*args, **kwargs)

        # Fallback for unmocked POST requests
        fallback_response = MagicMock(spec=requests.Response)
        fallback_response.status_code = 404
        fallback_response.json = MagicMock(return_value={"error": "Not Found - Unmocked POST URL"})
        fallback_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.HTTPError("404 Not Found")
        )
        return fallback_response

    monkeypatch.setattr(requests, "post", mock_post_router)
    return _add_mock_response


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mocks requests.get for context API calls."""
    mock_get_responses = {}

    def _add_mock_response(
        url_identifier,
        response_json=None,
        status_code=200,
        raise_for_status_exception=None,
        side_effect=None,
    ):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = status_code
        if response_json is not None:
            mock_response.json = MagicMock(return_value=response_json)
        else:
            mock_response.json = MagicMock(
                side_effect=requests.exceptions.JSONDecodeError("No JSON", "doc", 0)
            )

        if raise_for_status_exception:
            mock_response.raise_for_status = MagicMock(side_effect=raise_for_status_exception)
        else:
            mock_response.raise_for_status = MagicMock()

        if side_effect:
            mock_get_responses[url_identifier] = MagicMock(side_effect=side_effect)
        else:
            mock_get_responses[url_identifier] = MagicMock(return_value=mock_response)

    def mock_get_router(*args, **kwargs):
        url = args[0]
        if "context/" in url:
            if "context/" in mock_get_responses:
                return mock_get_responses["context/"](*args, **kwargs)

        # Fallback for unmocked GET requests
        fallback_response = MagicMock(spec=requests.Response)
        fallback_response.status_code = 404
        fallback_response.json = MagicMock(return_value={"error": "Not Found - Unmocked GET URL"})
        fallback_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.HTTPError("404 Not Found")
        )
        return fallback_response

    monkeypatch.setattr(requests, "get", mock_get_router)
    return _add_mock_response


# --- SDK Initialization Tests ---


def test_sdk_valid_initialization_refresh_token():
    """Test valid SDK init with user_id and refresh_token."""
    sdk = AlationAIAgentSDK(
        base_url=MOCK_BASE_URL, user_id=MOCK_USER_ID, refresh_token=MOCK_REFRESH_TOKEN
    )
    assert sdk.api.auth_method == AUTH_METHOD_REFRESH_TOKEN
    assert sdk.api.user_id == MOCK_USER_ID


def test_sdk_valid_initialization_service_account():
    """Test valid SDK init with client_id and client_secret."""
    sdk = AlationAIAgentSDK(
        base_url=MOCK_BASE_URL, client_id=MOCK_CLIENT_ID, client_secret=MOCK_CLIENT_SECRET
    )
    assert sdk.api.auth_method == AUTH_METHOD_SERVICE_ACCOUNT
    assert sdk.api.client_id == MOCK_CLIENT_ID


def test_sdk_initialization_service_account_priority():
    """Test SDK defaults to service account if all credentials provided."""
    sdk = AlationAIAgentSDK(
        base_url=MOCK_BASE_URL,
        user_id=MOCK_USER_ID,
        refresh_token=MOCK_REFRESH_TOKEN,
        client_id=MOCK_CLIENT_ID,
        client_secret=MOCK_CLIENT_SECRET,
    )
    assert sdk.api.auth_method == AUTH_METHOD_SERVICE_ACCOUNT


@pytest.mark.parametrize(
    "init_kwargs, expected_error_message_part",
    [
        # --- Base URL Validation ---
        (
            {"base_url": None, "user_id": MOCK_USER_ID, "refresh_token": MOCK_REFRESH_TOKEN},
            "base_url must be a non-empty string",
        ),
        # --- "Missing authentication credentials" ---
        # (Neither SA nor RT creds are fully and correctly provided to select an auth path)
        (
            {"base_url": MOCK_BASE_URL},  # Only base_url
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
        (  # Incomplete RT (missing refresh_token), no SA
            {"base_url": MOCK_BASE_URL, "user_id": MOCK_USER_ID},
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
        (  # Incomplete RT (missing user_id), no SA
            {"base_url": MOCK_BASE_URL, "refresh_token": MOCK_REFRESH_TOKEN},
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
        (  # Incomplete SA (missing client_secret), no RT
            {"base_url": MOCK_BASE_URL, "client_id": MOCK_CLIENT_ID},
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
        (  # Incomplete SA (missing client_id), no RT
            {"base_url": MOCK_BASE_URL, "client_secret": MOCK_CLIENT_SECRET},
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
        (  # Both RT and SA creds are individually incomplete
            {"base_url": MOCK_BASE_URL, "user_id": MOCK_USER_ID, "client_id": MOCK_CLIENT_ID},
            "Missing authentication credentials. Provide either (user_id and refresh_token) or (client_id and client_secret).",
        ),
    ],
)
def test_sdk_invalid_initialization_combinations(init_kwargs, expected_error_message_part):
    """Test various invalid SDK initialization scenarios."""
    with pytest.raises(ValueError) as excinfo:
        AlationAIAgentSDK(**init_kwargs)
    assert expected_error_message_part in str(excinfo.value)


def test_get_context_token_reuse(mock_requests_post, mock_requests_get):
    """Test that a valid token is reused."""
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_get("context/", response_json=CONTEXT_RESPONSE_SUCCESS)
    sdk = AlationAIAgentSDK(
        base_url=MOCK_BASE_URL, user_id=MOCK_USER_ID, refresh_token=MOCK_REFRESH_TOKEN
    )

    initial_time = (
        datetime.strptime(REFRESH_TOKEN_EXPIRES_AT, "%Y-%m-%dT%H:%M:%S.%fZ")
        .replace(tzinfo=timezone.utc)
        .timestamp()
        - 1000
    )
    time_after_first_call = initial_time + 10

    with patch("time.time") as mock_time:
        mock_time.return_value = initial_time
        sdk.get_context("first question")

        with patch.object(
            sdk.api,
            "_generate_access_token_with_refresh_token",
            wraps=sdk.api._generate_access_token_with_refresh_token,
        ) as spy_gen_token:
            mock_time.return_value = time_after_first_call
            sdk.get_context("second question")
            spy_gen_token.assert_not_called()


def test_get_context_token_refresh_on_expiry(mock_requests_post, mock_requests_get):
    """Test that token is refreshed if expired."""
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_get("context/", response_json=CONTEXT_RESPONSE_SUCCESS)
    sdk = AlationAIAgentSDK(
        base_url=MOCK_BASE_URL, user_id=MOCK_USER_ID, refresh_token=MOCK_REFRESH_TOKEN
    )

    with patch.object(
        sdk.api,
        "_generate_access_token_with_refresh_token",
        wraps=sdk.api._generate_access_token_with_refresh_token,
    ) as spy_gen_token:
        time_at_first_gen = (
            datetime.strptime(REFRESH_TOKEN_EXPIRES_AT, "%Y-%m-%dT%H:%M:%S.%fZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
            - timedelta(hours=24).total_seconds()
            - 100
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = time_at_first_gen
            sdk.get_context("first question, generates token")
            spy_gen_token.assert_called_once()

            time_after_expiry = sdk.api.token_expiry - 50
            mock_time.return_value = time_after_expiry

            sdk.get_context("second question, should refresh token")
            assert spy_gen_token.call_count == 2
