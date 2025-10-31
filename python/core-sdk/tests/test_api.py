import pytest
import requests
from unittest.mock import MagicMock, patch

from alation_ai_agent_sdk.api import (
    AlationAPI,
    AUTH_METHOD_SERVICE_ACCOUNT,
    AUTH_METHOD_BEARER_TOKEN,
    AUTH_METHOD_SESSION,
    DEFAULT_CONNECT_TIMEOUT_IN_SECONDS,
    DEFAULT_READ_TIMEOUT_IN_SECONDS,
)
from alation_ai_agent_sdk.types import (
    ServiceAccountAuthParams,
    BearerTokenAuthParams,
    SessionAuthParams,
)
from alation_ai_agent_sdk.errors import AlationAPIError
from alation_ai_agent_sdk.utils import SDK_VERSION


# --- Mock API Responses & Constants ---
MOCK_BASE_URL = "https://mock-alation-instance.com"
MOCK_CLIENT_ID = "test-client-id"
MOCK_CLIENT_SECRET = "test-client-secret"
MOCK_ACCESS_TOKEN = "test-access-token"
MOCK_SESSION_COOKIE = "sessionid=test_session_cookie_value"


@pytest.fixture
def api_instance():
    """Create a mock AlationAPI instance with service account auth."""
    with patch.object(AlationAPI, "_fetch_and_cache_instance_info"):
        api = AlationAPI(
            base_url=MOCK_BASE_URL,
            auth_method=AUTH_METHOD_SERVICE_ACCOUNT,
            auth_params=ServiceAccountAuthParams(MOCK_CLIENT_ID, MOCK_CLIENT_SECRET),
            skip_instance_info=True,
        )
        api.access_token = MOCK_ACCESS_TOKEN
        return api


@pytest.fixture
def bearer_token_api_instance():
    """Create a mock AlationAPI instance with bearer token auth."""
    with patch.object(AlationAPI, "_fetch_and_cache_instance_info"):
        api = AlationAPI(
            base_url=MOCK_BASE_URL,
            auth_method=AUTH_METHOD_BEARER_TOKEN,
            auth_params=BearerTokenAuthParams(MOCK_ACCESS_TOKEN),
            skip_instance_info=True,
        )
        return api


@pytest.fixture
def session_api_instance():
    """Create a mock AlationAPI instance with session auth."""
    with patch.object(AlationAPI, "_fetch_and_cache_instance_info"):
        api = AlationAPI(
            base_url=MOCK_BASE_URL,
            auth_method=AUTH_METHOD_SESSION,
            auth_params=SessionAuthParams(MOCK_SESSION_COOKIE),
            skip_instance_info=True,
        )
        return api


# --- Tests for _fetch_and_cache_instance_info ---


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_and_cache_instance_info_success(mock_get, api_instance):
    """Test successful fetching and caching of instance info."""
    # Mock successful license response
    license_response = MagicMock()
    license_response.raise_for_status.return_value = None
    license_response.json.return_value = {
        "is_cloud": True,
        "license_type": "enterprise",
    }

    # Mock successful version response
    version_response = MagicMock()
    version_response.raise_for_status.return_value = None
    version_response.json.return_value = {
        "ALATION_RELEASE_NAME": "2025.1.2",
        "version": "1.0",
    }

    # Configure mock_get to return different responses based on URL
    def side_effect(url, **kwargs):
        if "license" in url:
            return license_response
        elif "full_version" in url:
            return version_response
        return MagicMock()

    mock_get.side_effect = side_effect

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(api_instance, "_get_request_headers", return_value={}),
    ):
        api_instance._fetch_and_cache_instance_info()

        assert api_instance.is_cloud is True
        assert api_instance.alation_release_name == "2025.1.2"
        assert api_instance.alation_license_info == {
            "is_cloud": True,
            "license_type": "enterprise",
        }
        assert api_instance.alation_version_info == {
            "ALATION_RELEASE_NAME": "2025.1.2",
            "version": "1.0",
        }


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_and_cache_instance_info_license_failure(mock_get, api_instance):
    """Test handling of license fetch failure."""
    # Mock license failure
    license_response = MagicMock()
    license_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

    # Mock successful version response
    version_response = MagicMock()
    version_response.raise_for_status.return_value = None
    version_response.json.return_value = {"ALATION_RELEASE_NAME": "2025.1.2"}

    def side_effect(url, **kwargs):
        if "license" in url:
            return license_response
        elif "full_version" in url:
            return version_response
        return MagicMock()

    mock_get.side_effect = side_effect

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(api_instance, "_get_request_headers", return_value={}),
    ):
        api_instance._fetch_and_cache_instance_info()

        assert api_instance.is_cloud is None
        assert api_instance.alation_license_info is None
        assert api_instance.alation_release_name == "2025.1.2"


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_and_cache_instance_info_version_failure(mock_get, api_instance):
    """Test handling of version fetch failure."""
    # Mock successful license response
    license_response = MagicMock()
    license_response.raise_for_status.return_value = None
    license_response.json.return_value = {"is_cloud": False}

    # Mock version failure
    version_response = MagicMock()
    version_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500")

    def side_effect(url, **kwargs):
        if "license" in url:
            return license_response
        elif "full_version" in url:
            return version_response
        return MagicMock()

    mock_get.side_effect = side_effect

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(api_instance, "_get_request_headers", return_value={}),
    ):
        api_instance._fetch_and_cache_instance_info()

        assert api_instance.is_cloud is False
        assert api_instance.alation_release_name is None
        assert api_instance.alation_version_info is None


# --- Tests for _get_response_meta ---


def test_get_response_meta_with_entitlement_warning(api_instance):
    """Test extracting meta information when entitlement warning is present."""
    mock_response = MagicMock()
    mock_response.headers = {
        "X-Entitlement-Warning": "Approaching limit",
        "X-Entitlement-Limit": "1000",
        "X-Entitlement-Usage": "950",
        "Other-Header": "value",
    }

    result = api_instance._get_response_meta(mock_response)

    expected = {
        "X-Entitlement-Limit": "1000",
        "X-Entitlement-Usage": "950",
        "X-Entitlement-Warning": "Approaching limit",
    }
    assert result == expected


def test_get_response_meta_without_entitlement_warning(api_instance):
    """Test that no meta information is returned when entitlement warning is absent."""
    mock_response = MagicMock()
    mock_response.headers = {
        "X-Entitlement-Limit": "1000",
        "X-Entitlement-Usage": "950",
        "Other-Header": "value",
    }

    result = api_instance._get_response_meta(mock_response)

    assert result is None


def test_get_response_meta_no_headers(api_instance):
    """Test handling when response has no headers."""
    mock_response = MagicMock()
    mock_response.headers = {}

    result = api_instance._get_response_meta(mock_response)

    assert result is None


def test_get_response_meta_none_headers(api_instance):
    """Test handling when response headers is None."""
    mock_response = MagicMock()
    del mock_response.headers  # This will cause getattr to return {}

    result = api_instance._get_response_meta(mock_response)

    assert result is None


# --- Tests for _format_successful_response ---


def test_format_successful_response_dict_with_meta(api_instance):
    """Test formatting successful response as dict with meta information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test", "key": "value"}

    meta_info = {
        "X-Entitlement-Limit": "1000",
        "X-Entitlement-Usage": "950",
        "X-Entitlement-Warning": "Approaching limit",
    }

    with patch.object(api_instance, "_get_response_meta", return_value=meta_info):
        result = api_instance._format_successful_response(mock_response)

    expected = {"data": "test", "key": "value", "_meta": {"headers": meta_info}}
    assert result == expected


def test_format_successful_response_list_with_meta(api_instance):
    """Test formatting successful response as list with meta information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"item1": "data1"}, {"item2": "data2"}]

    meta_info = {
        "X-Entitlement-Limit": "1000",
        "X-Entitlement-Usage": "950",
        "X-Entitlement-Warning": "Approaching limit",
    }

    with patch.object(api_instance, "_get_response_meta", return_value=meta_info):
        result = api_instance._format_successful_response(mock_response)

    expected = {
        "results": [{"item1": "data1"}, {"item2": "data2"}],
        "_meta": {"headers": meta_info},
    }
    assert result == expected


def test_format_successful_response_without_meta(api_instance):
    """Test formatting successful response without meta information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    with patch.object(api_instance, "_get_response_meta", return_value=None):
        result = api_instance._format_successful_response(mock_response)

    assert result == {"data": "test"}


def test_format_successful_response_non_success_status_code(api_instance):
    """Test formatting response with non-success status code."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Bad request"}

    with patch.object(api_instance, "_get_response_meta", return_value=None):
        result = api_instance._format_successful_response(mock_response)

    assert result == {"error": "Bad request"}


# --- Tests for _get_request_headers ---


def test_get_request_headers_service_account_auth(api_instance):
    """Test request headers for service account authentication."""
    api_instance.dist_version = "test-dist-1.0"

    result = api_instance._get_request_headers()

    expected = {
        "Accept": "application/json",
        "User-Agent": f"test-dist-1.0/sdk-{SDK_VERSION}",
        "Token": MOCK_ACCESS_TOKEN,
    }
    assert result == expected


def test_get_request_headers_session_auth(session_api_instance):
    """Test request headers for session authentication."""
    session_api_instance.dist_version = None

    result = session_api_instance._get_request_headers()

    expected_headers = {"Accept": "application/json", "Cookie": MOCK_SESSION_COOKIE}
    if SDK_VERSION:
        expected_headers["User-Agent"] = f"sdk-{SDK_VERSION}"

    assert result == expected_headers


def test_get_request_headers_bearer_token_auth(bearer_token_api_instance):
    """Test request headers for bearer token authentication."""
    bearer_token_api_instance.dist_version = "mcp-2.0"

    result = bearer_token_api_instance._get_request_headers()

    expected = {
        "Accept": "application/json",
        "User-Agent": f"mcp-2.0/sdk-{SDK_VERSION}",
        "Token": MOCK_ACCESS_TOKEN,
    }
    assert result == expected


def test_get_request_headers_with_overrides(api_instance):
    """Test request headers with header overrides."""
    api_instance.dist_version = None
    overrides = {"Content-Type": "application/json", "Custom-Header": "custom-value"}

    result = api_instance._get_request_headers(header_overrides=overrides)

    expected = {
        "Accept": "application/json",
        "Token": MOCK_ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Custom-Header": "custom-value",
    }
    if SDK_VERSION:
        expected["User-Agent"] = f"sdk-{SDK_VERSION}"

    assert result == expected


def test_get_request_headers_no_access_token(api_instance):
    """Test request headers when access token is None."""
    api_instance.access_token = None
    api_instance.dist_version = None

    result = api_instance._get_request_headers()

    expected = {"Accept": "application/json"}
    if SDK_VERSION:
        expected["User-Agent"] = f"sdk-{SDK_VERSION}"

    assert result == expected


# --- Tests for _get_streaming_request_headers ---


def test_get_streaming_request_headers_service_account(api_instance):
    """Test streaming request headers for service account authentication."""
    api_instance.dist_version = "test-dist-1.0"

    result = api_instance._get_streaming_request_headers()

    expected = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOCK_ACCESS_TOKEN}",
        "User-Agent": f"test-dist-1.0/sdk-{SDK_VERSION}",
        "Token": MOCK_ACCESS_TOKEN,
    }
    assert result == expected


def test_get_streaming_request_headers_bearer_token(bearer_token_api_instance):
    """Test streaming request headers for bearer token authentication."""
    result = bearer_token_api_instance._get_streaming_request_headers()

    expected_base = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOCK_ACCESS_TOKEN}",
        "Token": MOCK_ACCESS_TOKEN,
    }
    if SDK_VERSION:
        expected_base["User-Agent"] = f"sdk-{SDK_VERSION}"

    assert result == expected_base


def test_get_streaming_request_headers_session_auth(session_api_instance):
    """Test streaming request headers for session authentication."""
    result = session_api_instance._get_streaming_request_headers()

    expected_base = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Cookie": MOCK_SESSION_COOKIE,
    }
    if SDK_VERSION:
        expected_base["User-Agent"] = f"sdk-{SDK_VERSION}"

    assert result == expected_base


# --- Tests for _get_streaming_timeouts ---


def test_get_streaming_timeouts_defaults(api_instance):
    """Test streaming timeouts with default values."""
    result = api_instance._get_streaming_timeouts()

    expected = (DEFAULT_CONNECT_TIMEOUT_IN_SECONDS, DEFAULT_READ_TIMEOUT_IN_SECONDS)
    assert result == expected


def test_get_streaming_timeouts_custom(api_instance):
    """Test streaming timeouts with custom values."""
    result = api_instance._get_streaming_timeouts(connect_timeout=30, read_timeout=600)

    expected = (30, 600)
    assert result == expected


def test_get_streaming_timeouts_partial_custom(api_instance):
    """Test streaming timeouts with only one custom value."""
    result = api_instance._get_streaming_timeouts(connect_timeout=45)

    expected = (45, DEFAULT_READ_TIMEOUT_IN_SECONDS)
    assert result == expected


def test_get_streaming_timeouts_only_read_timeout(api_instance):
    """Test streaming timeouts with only read timeout specified."""
    result = api_instance._get_streaming_timeouts(read_timeout=900)

    expected = (DEFAULT_CONNECT_TIMEOUT_IN_SECONDS, 900)
    assert result == expected


# --- Tests for _iter_sse_response ---


def test_iter_sse_response_success(api_instance):
    """Test successful iteration over SSE response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_lines.return_value = [
        b'data: {"event": "start", "data": "test1"}',
        b"",
        b'data: {"event": "end", "data": "test2"}',
        b"event: heartbeat",
        b'data: {"event": "final", "data": "test3"}',
    ]

    result = list(api_instance._iter_sse_response(mock_response))

    expected = [
        {"event": "start", "data": "test1"},
        {"event": "end", "data": "test2"},
        {"event": "final", "data": "test3"},
    ]
    assert result == expected


def test_iter_sse_response_invalid_json(api_instance):
    """Test handling of invalid JSON in SSE response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_lines.return_value = [
        b'data: {"valid": "json"}',
        b"data: invalid json string",
        b'data: {"another": "valid"}',
    ]

    result = list(api_instance._iter_sse_response(mock_response))

    expected = [{"valid": "json"}, {"another": "valid"}]
    assert result == expected


def test_iter_sse_response_empty_lines(api_instance):
    """Test handling of empty lines in SSE response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_lines.return_value = [
        b"",
        b'data: {"test": "data"}',
        b"",
        b"",
        b'data: {"more": "data"}',
    ]

    result = list(api_instance._iter_sse_response(mock_response))

    expected = [{"test": "data"}, {"more": "data"}]
    assert result == expected


def test_iter_sse_response_http_error(api_instance):
    """Test handling of HTTP error in SSE response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error"
    )

    with pytest.raises(requests.exceptions.HTTPError):
        list(api_instance._iter_sse_response(mock_response))


# --- Tests for _sse_stream_or_last_event ---


def test_sse_stream_or_last_event_streaming_mode(api_instance):
    """Test SSE streaming in streaming mode."""
    mock_response = MagicMock()

    # Enable streaming mode for this test
    api_instance.enable_streaming = True

    test_events = [
        {"event": "start", "data": "test1"},
        {"event": "middle", "data": "test2"},
        {"event": "end", "data": "test3"},
    ]

    with patch.object(
        api_instance, "_iter_sse_response", return_value=iter(test_events)
    ):
        result = list(api_instance._sse_stream_or_last_event(mock_response))

    assert result == test_events


def test_sse_stream_or_last_event_non_streaming_mode(api_instance):
    """Test SSE streaming in non-streaming mode (returns only last event)."""
    mock_response = MagicMock()

    test_events = [
        {"event": "start", "data": "test1"},
        {"event": "middle", "data": "test2"},
        {"event": "end", "data": "test3"},
    ]

    with patch.object(
        api_instance, "_iter_sse_response", return_value=iter(test_events)
    ):
        result = list(api_instance._sse_stream_or_last_event(mock_response))

    assert result == [{"event": "end", "data": "test3"}]


def test_sse_stream_or_last_event_empty_response(api_instance):
    """Test SSE streaming with empty response."""
    mock_response = MagicMock()

    with patch.object(api_instance, "_iter_sse_response", return_value=iter([])):
        result = list(api_instance._sse_stream_or_last_event(mock_response))

    assert result == [None]


# --- Tests for _fetch_marketplace_id ---


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_marketplace_id_success(mock_get, api_instance):
    """Test successful marketplace ID fetch."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"default_marketplace": "marketplace-123"}
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer token"}
    result = api_instance._fetch_marketplace_id(headers)

    assert result == "marketplace-123"
    mock_get.assert_called_once_with(
        f"{MOCK_BASE_URL}/api/v1/setting/marketplace/", headers=headers, timeout=30
    )


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_marketplace_id_missing_id(mock_get, api_instance):
    """Test handling when marketplace ID is missing from response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"other_field": "value"}
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer token"}

    with pytest.raises(AlationAPIError) as exc_info:
        api_instance._fetch_marketplace_id(headers)

    assert "Marketplace ID not found in response" in str(exc_info.value)
    assert exc_info.value.reason == "Missing Marketplace ID"


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_marketplace_id_empty_id(mock_get, api_instance):
    """Test handling when marketplace ID is empty."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"default_marketplace": ""}
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer token"}

    with pytest.raises(AlationAPIError) as exc_info:
        api_instance._fetch_marketplace_id(headers)

    assert "Marketplace ID not found in response" in str(exc_info.value)


@patch("alation_ai_agent_sdk.api.requests.get")
def test_fetch_marketplace_id_request_exception(mock_get, api_instance):
    """Test handling of request exception during marketplace ID fetch."""
    mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

    with patch.object(api_instance, "_handle_request_error") as mock_handle_error:
        mock_handle_error.side_effect = AlationAPIError("Handled error")

        headers = {"Authorization": "Bearer token"}

        with pytest.raises(AlationAPIError):
            api_instance._fetch_marketplace_id(headers)

        mock_handle_error.assert_called_once()


# --- Tests for _safe_sse_post_request ---


@patch("alation_ai_agent_sdk.api.requests.post")
def test_safe_sse_post_request_success(mock_post, api_instance):
    """Test successful SSE POST request."""
    # Mock response
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)

    # Mock the context manager
    mock_post.return_value = mock_response

    test_events = [{"event": "test", "data": "response"}]

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(
            api_instance,
            "_get_streaming_request_headers",
            return_value={"Auth": "token"},
        ),
        patch.object(api_instance, "_get_streaming_timeouts", return_value=(60, 300)),
        patch.object(api_instance, "_get_response_meta", return_value=None),
        patch.object(
            api_instance, "_sse_stream_or_last_event", return_value=iter(test_events)
        ),
    ):
        result = list(
            api_instance._safe_sse_post_request(
                tool_name="test_tool",
                url="https://test.com/api",
                payload={"query": "test"},
            )
        )

    assert result == test_events
    mock_post.assert_called_once()


@patch("alation_ai_agent_sdk.api.requests.post")
def test_safe_sse_post_request_with_response_meta(mock_post, api_instance):
    """Test SSE POST request with response meta information."""
    # Mock response
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)

    mock_post.return_value = mock_response

    test_events = [{"event": "test", "data": "response"}]
    meta_info = {"X-Entitlement-Warning": "Approaching limit"}

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(
            api_instance,
            "_get_streaming_request_headers",
            return_value={"Auth": "token"},
        ),
        patch.object(api_instance, "_get_streaming_timeouts", return_value=(60, 300)),
        patch.object(api_instance, "_get_response_meta", return_value=meta_info),
        patch.object(
            api_instance, "_sse_stream_or_last_event", return_value=iter(test_events)
        ),
    ):
        result = list(
            api_instance._safe_sse_post_request(
                tool_name="test_tool",
                url="https://test.com/api",
                payload={"query": "test"},
            )
        )

    assert result == test_events


@patch("alation_ai_agent_sdk.api.requests.post")
def test_safe_sse_post_request_read_timeout(mock_post, api_instance):
    """Test handling of read timeout in SSE POST request."""
    mock_post.side_effect = requests.exceptions.ReadTimeout("Read timeout")

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(
            api_instance,
            "_get_streaming_request_headers",
            return_value={"Auth": "token"},
        ),
        patch.object(api_instance, "_get_streaming_timeouts", return_value=(60, 300)),
        patch.object(api_instance, "_handle_request_error") as mock_handle_error,
    ):
        mock_handle_error.side_effect = AlationAPIError("Read timeout handled")

        with pytest.raises(AlationAPIError):
            list(
                api_instance._safe_sse_post_request(
                    tool_name="test_tool",
                    url="https://test.com/api",
                    payload={"query": "test"},
                )
            )

        mock_handle_error.assert_called_once()


@patch("alation_ai_agent_sdk.api.requests.post")
def test_safe_sse_post_request_connect_timeout(mock_post, api_instance):
    """Test handling of connection timeout in SSE POST request."""
    mock_post.side_effect = requests.exceptions.ConnectTimeout("Connection timeout")

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(
            api_instance,
            "_get_streaming_request_headers",
            return_value={"Auth": "token"},
        ),
        patch.object(api_instance, "_get_streaming_timeouts", return_value=(60, 300)),
        patch.object(api_instance, "_handle_request_error") as mock_handle_error,
    ):
        mock_handle_error.side_effect = AlationAPIError("Connection timeout handled")

        with pytest.raises(AlationAPIError):
            list(
                api_instance._safe_sse_post_request(
                    tool_name="test_tool",
                    url="https://test.com/api",
                    payload={"query": "test"},
                )
            )

        mock_handle_error.assert_called_once()


@patch("alation_ai_agent_sdk.api.requests.post")
def test_safe_sse_post_request_general_request_exception(mock_post, api_instance):
    """Test handling of general request exception in SSE POST request."""
    mock_post.side_effect = requests.exceptions.RequestException("General error")

    with (
        patch.object(api_instance, "_with_valid_auth"),
        patch.object(
            api_instance,
            "_get_streaming_request_headers",
            return_value={"Auth": "token"},
        ),
        patch.object(api_instance, "_get_streaming_timeouts", return_value=(60, 300)),
        patch.object(api_instance, "_handle_request_error") as mock_handle_error,
    ):
        mock_handle_error.side_effect = AlationAPIError("General error handled")

        with pytest.raises(AlationAPIError):
            list(
                api_instance._safe_sse_post_request(
                    tool_name="test_tool",
                    url="https://test.com/api",
                    payload={"query": "test"},
                )
            )

        mock_handle_error.assert_called_once()


def test_safe_sse_post_request_disallowed_auth_method(api_instance):
    """Test that disallowed auth methods are properly checked."""
    with patch.object(api_instance, "_with_valid_auth") as mock_auth:
        mock_auth.side_effect = AlationAPIError("Auth method not allowed")

        with pytest.raises(AlationAPIError):
            list(
                api_instance._safe_sse_post_request(
                    tool_name="test_tool",
                    url="https://test.com/api",
                    payload={"query": "test"},
                )
            )

        # Verify that _with_valid_auth was called with the disallowed methods
        mock_auth.assert_called_once_with(
            disallowed_methods=["user_account", AUTH_METHOD_SESSION]
        )


# --- Tests for _is_likely_json_value ---


def test_is_likely_json_value_object_true(api_instance):
    """Test that strings that look like JSON objects return True."""
    assert api_instance._is_likely_json_value('{"key": "value"}') is True
    assert api_instance._is_likely_json_value("{}") is True
    assert api_instance._is_likely_json_value('{"nested": {"key": "value"}}') is True


def test_is_likely_json_value_array_true(api_instance):
    """Test that strings that look like JSON arrays return True."""
    assert api_instance._is_likely_json_value("[]") is True
    assert api_instance._is_likely_json_value("[1, 2, 3]") is True
    assert api_instance._is_likely_json_value('[{"key": "value"}]') is True


def test_is_likely_json_value_false_cases(api_instance):
    """Test that non-JSON-like strings return False."""
    assert api_instance._is_likely_json_value("not json") is False
    assert api_instance._is_likely_json_value("123") is False
    assert api_instance._is_likely_json_value("true") is False
    assert api_instance._is_likely_json_value("null") is False
    assert api_instance._is_likely_json_value('"string"') is False
    assert api_instance._is_likely_json_value("{not closed") is False
    assert api_instance._is_likely_json_value("not closed}") is False
    assert api_instance._is_likely_json_value("[not closed") is False
    assert api_instance._is_likely_json_value("not closed]") is False


def test_is_likely_json_value_non_string(api_instance):
    """Test that non-string values return False."""
    assert api_instance._is_likely_json_value(123) is False
    assert api_instance._is_likely_json_value(None) is False
    assert api_instance._is_likely_json_value([]) is False
    assert api_instance._is_likely_json_value({}) is False
    assert api_instance._is_likely_json_value(True) is False


# --- Tests for _decode_json_string ---


def test_decode_json_string_valid_object(api_instance):
    """Test decoding valid JSON object strings."""
    input_str = '{"key": "value", "number": 42}'
    expected = {"key": "value", "number": 42}
    result = api_instance._decode_json_string(input_str)
    assert result == expected


def test_decode_json_string_valid_array(api_instance):
    """Test decoding valid JSON array strings."""
    input_str = '[1, 2, {"key": "value"}]'
    expected = [1, 2, {"key": "value"}]
    result = api_instance._decode_json_string(input_str)
    assert result == expected


def test_decode_json_string_invalid_json(api_instance):
    """Test that invalid JSON returns the original string."""
    invalid_json = '{"invalid": json}'
    result = api_instance._decode_json_string(invalid_json)
    assert result == invalid_json


def test_decode_json_string_not_json_like(api_instance):
    """Test that non-JSON-like strings are returned unchanged."""
    input_str = "just a regular string"
    result = api_instance._decode_json_string(input_str)
    assert result == input_str


def test_decode_json_string_non_string_input(api_instance):
    """Test that non-string inputs are returned unchanged."""
    inputs = [123, None, [], {}, True]
    for input_val in inputs:
        result = api_instance._decode_json_string(input_val)
        assert result == input_val


def test_decode_json_string_empty_object_array(api_instance):
    """Test decoding empty JSON objects and arrays."""
    assert api_instance._decode_json_string("{}") == {}
    assert api_instance._decode_json_string("[]") == []


# --- Tests for _shallow_decode_collection ---


def test_shallow_decode_collection_dict_with_json_strings(api_instance):
    """Test shallow decoding of dictionary with JSON string values."""
    input_dict = {
        "regular_key": "regular_value",
        "json_key": '{"nested": "value"}',
        "array_key": "[1, 2, 3]",
        "number_key": 42,
    }

    result = api_instance._shallow_decode_collection(input_dict)

    expected = {
        "regular_key": "regular_value",
        "json_key": {"nested": "value"},
        "array_key": [1, 2, 3],
        "number_key": 42,
    }
    assert result == expected


def test_shallow_decode_collection_list_with_json_strings(api_instance):
    """Test shallow decoding of list with JSON string values."""
    input_list = ["regular_string", '{"object": "value"}', "[1, 2, 3]", 42, None]

    result = api_instance._shallow_decode_collection(input_list)

    expected = ["regular_string", {"object": "value"}, [1, 2, 3], 42, None]
    assert result == expected


def test_shallow_decode_collection_non_collection(api_instance):
    """Test that non-collection objects are returned unchanged."""
    test_values = ["string", 123, None, True]
    for value in test_values:
        result = api_instance._shallow_decode_collection(value)
        assert result == value


def test_shallow_decode_collection_empty_collections(api_instance):
    """Test shallow decoding of empty collections."""
    assert api_instance._shallow_decode_collection({}) == {}
    assert api_instance._shallow_decode_collection([]) == []


def test_shallow_decode_collection_invalid_json_strings(api_instance):
    """Test that invalid JSON strings in collections remain unchanged."""
    input_dict = {
        "invalid_json": '{"invalid": json}',
        "valid_json": '{"valid": "json"}',
    }

    result = api_instance._shallow_decode_collection(input_dict)

    expected = {"invalid_json": '{"invalid": json}', "valid_json": {"valid": "json"}}
    assert result == expected


# --- Tests for _decode_nested_json ---


def test_decode_nested_json_valid_text_part(api_instance):
    """Test decoding nested JSON with valid text part."""
    input_data = {
        "model_message": {
            "parts": [
                {
                    "part_kind": "text",
                    "content": '{"data": "test", "nested": {"key": "value"}}',
                }
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    expected_parts = [{"data": "test", "nested": {"key": "value"}}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_with_shallow_decode(api_instance):
    """Test that decoded collections get shallow decoded."""
    input_data = {
        "model_message": {
            "parts": [
                {
                    "part_kind": "text",
                    "content": '{"json_string": "{\\"nested\\": \\"value\\"}", "regular": "data"}',
                }
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    expected_parts = [{"json_string": {"nested": "value"}, "regular": "data"}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_non_text_part(api_instance):
    """Test that non-text parts are left unchanged."""
    input_data = {
        "model_message": {
            "parts": [
                {"part_kind": "image", "content": "image_data"},
                {"part_kind": "text", "content": '{"test": "data"}'},
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    expected_parts = [{"part_kind": "image", "content": "image_data"}, {"test": "data"}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_invalid_json_content(api_instance):
    """Test that invalid JSON content leaves the part unchanged."""
    input_data = {
        "model_message": {
            "parts": [{"part_kind": "text", "content": '{"invalid": json}'}]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    # Should remain unchanged since JSON is invalid
    expected_parts = [{"part_kind": "text", "content": '{"invalid": json}'}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_non_json_content(api_instance):
    """Test that non-JSON content leaves the part unchanged."""
    input_data = {
        "model_message": {
            "parts": [{"part_kind": "text", "content": "regular text content"}]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    # Should remain unchanged since content is not JSON-like
    expected_parts = [{"part_kind": "text", "content": "regular text content"}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_no_model_message(api_instance):
    """Test that data without model_message is returned unchanged."""
    input_data = {"other_field": "value"}
    result = api_instance._decode_nested_json(input_data)
    assert result == input_data


def test_decode_nested_json_no_parts(api_instance):
    """Test that model_message without parts is returned unchanged."""
    input_data = {"model_message": {"other_field": "value"}}
    result = api_instance._decode_nested_json(input_data)
    assert result == input_data


def test_decode_nested_json_non_dict_parts(api_instance):
    """Test handling of non-dict entries in parts list."""
    input_data = {
        "model_message": {
            "parts": [
                "not_a_dict",
                {"part_kind": "text", "content": '{"test": "data"}'},
                None,
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    # Non-dict entries should be skipped, only the valid text part should be processed
    expected_parts = [{"test": "data"}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_non_string_content(api_instance):
    """Test that text parts with non-string content are left unchanged."""
    input_data = {
        "model_message": {
            "parts": [
                {
                    "part_kind": "text",
                    "content": 123,  # Non-string content
                }
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    expected_parts = [{"part_kind": "text", "content": 123}]
    assert result["model_message"]["parts"] == expected_parts


def test_decode_nested_json_array_content(api_instance):
    """Test decoding text part with JSON array content."""
    input_data = {
        "model_message": {
            "parts": [
                {
                    "part_kind": "text",
                    "content": '[{"item": "value1"}, {"item": "value2"}]',
                }
            ]
        }
    }

    result = api_instance._decode_nested_json(input_data)

    expected_parts = [[{"item": "value1"}, {"item": "value2"}]]
    assert result["model_message"]["parts"] == expected_parts
