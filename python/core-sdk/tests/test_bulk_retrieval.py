import pytest
from unittest.mock import Mock, patch
from alation_ai_agent_sdk.tools import AlationBulkRetrievalTool
from alation_ai_agent_sdk.api import AlationAPI, AlationAPIError
from alation_ai_agent_sdk.types import ServiceAccountAuthParams


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def bulk_retrieval_tool(mock_api):
    """Creates an AlationBulkRetrievalTool with mock API."""
    return AlationBulkRetrievalTool(mock_api)


@pytest.fixture
def alation_api():
    """Creates a real AlationAPI instance for testing with HTTP mocking."""
    api = AlationAPI(
        base_url="https://test.alation.com",
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams("test_client", "test_secret"),
        skip_instance_info=True,
    )
    # Mock the token validation to avoid additional HTTP calls
    api.access_token = "mock_token"
    api._token_is_valid_on_server = Mock(return_value=True)
    return api


@pytest.fixture
def bulk_retrieval_tool_with_alation_api(alation_api):
    """Creates an AlationBulkRetrievalTool with AlationAPI instance for HTTP-level testing."""
    return AlationBulkRetrievalTool(alation_api)


def create_mock_response(
    json_data, status_code=200, headers=None, raise_for_status=False
):
    """Helper function to create a mock requests.Response object."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.headers = headers or {}
    mock_response.text = str(json_data)  # Add text attribute for error handling

    if raise_for_status:
        # Import here to avoid circular imports in test
        import requests

        http_error = requests.exceptions.HTTPError(f"{status_code} Client Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
    else:
        mock_response.raise_for_status.return_value = None

    return mock_response


def create_entitlement_headers(warning=None, limit=None, usage=None):
    """Helper function to create entitlement headers."""
    headers = {}
    if warning:
        headers["X-Entitlement-Warning"] = warning
    if limit:
        headers["X-Entitlement-Limit"] = str(limit)
    if usage:
        headers["X-Entitlement-Usage"] = str(usage)
    return headers


def test_bulk_retrieval_tool_run_success(bulk_retrieval_tool, mock_api):
    """Test successful bulk retrieval."""
    # Mock response
    mock_response = {
        "relevant_tables": [
            {
                "name": "customers",
                "description": "Customer data",
                "url": "https://alation.com/table/123",
            }
        ]
    }
    mock_api.get_bulk_objects_from_catalog.return_value = mock_response

    signature = {
        "table": {"fields_required": ["name", "description", "url"], "limit": 1}
    }

    result = bulk_retrieval_tool.run(signature)

    # Verify API was called correctly
    mock_api.get_bulk_objects_from_catalog.assert_called_once_with(signature)

    # Verify result
    assert result == mock_response
    assert "relevant_tables" in result
    assert len(result["relevant_tables"]) == 1
    assert result["relevant_tables"][0]["name"] == "customers"


def test_bulk_retrieval_tool_run_without_signature(bulk_retrieval_tool, mock_api):
    """Test that missing signature returns helpful error."""
    result = bulk_retrieval_tool.run()

    # Verify API was not called
    mock_api.get_bulk_objects_from_catalog.assert_not_called()

    # Verify error response
    assert "error" in result
    assert "Signature parameter is required" in result["error"]["message"]
    assert "example_signature" in result["error"]
    assert "table" in result["error"]["example_signature"]


def test_bulk_retrieval_tool_run_empty_signature(bulk_retrieval_tool, mock_api):
    """Test that empty signature returns helpful error."""
    result = bulk_retrieval_tool.run(signature={})

    # Verify API was not called
    mock_api.get_bulk_objects_from_catalog.assert_not_called()

    # Verify error response
    assert "error" in result
    assert "Signature parameter is required" in result["error"]["message"]


def test_bulk_retrieval_tool_run_api_error(bulk_retrieval_tool, mock_api):
    """Test handling of API errors."""
    # Mock API error
    api_error = AlationAPIError(
        message="Bad Request",
        status_code=400,
        reason="Bad Request",
        resolution_hint="Check signature format",
    )
    mock_api.get_bulk_objects_from_catalog.side_effect = api_error

    invalid_signature = {"unknown": {"fields_required": ["name"], "limit": 100}}

    result = bulk_retrieval_tool.run(invalid_signature)

    # Verify API was called
    mock_api.get_bulk_objects_from_catalog.assert_called_once_with(invalid_signature)

    # Verify error handling
    assert "error" in result
    assert result["error"]["message"] == "Bad Request"
    assert result["error"]["status_code"] == 400
    assert result["error"]["reason"] == "Bad Request"


@patch("alation_ai_agent_sdk.api.requests.get")
def test_bulk_retrieval_tool_run_usage_quota_warning(
    mock_requests_get, bulk_retrieval_tool_with_alation_api
):
    """Test handling of usage quota warning in the header."""
    # Mock response data
    mock_response_data = {
        "relevant_tables": [
            {
                "name": "orders",
                "description": "Order data",
                "url": "https://alation.com/table/456",
            }
        ]
    }

    # Create mock response with entitlement headers
    entitlement_headers = create_entitlement_headers(
        warning="You are at 94% of your quota. Enforcement starts at 120%.",
        limit=1000,
        usage=940,
    )
    mock_response = create_mock_response(
        mock_response_data, headers=entitlement_headers
    )
    mock_requests_get.return_value = mock_response

    signature = {
        "table": {"fields_required": ["name", "description", "url"], "limit": 1}
    }

    result = bulk_retrieval_tool_with_alation_api.run(signature)

    # Verify the requests.get was called
    mock_requests_get.assert_called_once()

    # Verify the response data
    assert "relevant_tables" in result
    assert len(result["relevant_tables"]) == 1
    assert result["relevant_tables"][0]["name"] == "orders"

    # Check that the _meta field was injected by _format_successful_response
    assert "_meta" in result
    assert "headers" in result["_meta"]
    assert (
        result["_meta"]["headers"]["X-Entitlement-Warning"]
        == "You are at 94% of your quota. Enforcement starts at 120%."
    )
    assert result["_meta"]["headers"]["X-Entitlement-Limit"] == "1000"
    assert result["_meta"]["headers"]["X-Entitlement-Usage"] == "940"


@patch("alation_ai_agent_sdk.api.requests.get")
def test_bulk_retrieval_tool_run_no_entitlement_warning(
    mock_requests_get, bulk_retrieval_tool_with_alation_api
):
    """Test that no entitlement warning does not add _meta field."""
    # Mock response data without any entitlement headers
    mock_response_data = {
        "relevant_tables": [
            {
                "name": "customers",
                "description": "Customer data",
                "url": "https://alation.com/table/123",
            }
        ]
    }

    # Create mock response without entitlement warning. Only limit and usage
    entitlement_headers = create_entitlement_headers(
        limit=1000,
        usage=1,
    )
    mock_response = create_mock_response(
        mock_response_data, headers=entitlement_headers
    )
    mock_requests_get.return_value = mock_response

    signature = {
        "table": {"fields_required": ["name", "description", "url"], "limit": 1}
    }

    result = bulk_retrieval_tool_with_alation_api.run(signature)

    # Verify the requests.get was called
    mock_requests_get.assert_called_once()

    # Verify the response data
    assert "relevant_tables" in result
    assert len(result["relevant_tables"]) == 1
    assert result["relevant_tables"][0]["name"] == "customers"

    # Check that no _meta field was added since there is no entitlement warning header
    assert "_meta" not in result


@patch("alation_ai_agent_sdk.api.requests.get")
def test_bulk_retrieval_tool_with_429_quota_reached(
    mock_requests_get, bulk_retrieval_tool_with_alation_api
):
    """Test that quota exceeded error is handled correctly."""
    # Mock response data for a 429 Too Many Requests response
    mock_response_data = {"error": "Entitlement quota exceeded"}

    # Create mock response with 429 status that raises HTTPError
    mock_response = create_mock_response(
        mock_response_data, status_code=429, raise_for_status=True
    )
    mock_requests_get.return_value = mock_response

    signature = {
        "table": {"fields_required": ["name", "description", "url"], "limit": 1}
    }

    result = bulk_retrieval_tool_with_alation_api.run(signature)

    # Verify the requests.get was called
    mock_requests_get.assert_called_once()

    # Verify that the error was handled by _handle_request_error and returned as an error dict
    assert "error" in result
    assert "status_code" in result["error"]
    assert result["error"]["status_code"] == 429
    assert result["error"]["reason"] == "License Quota Exceeded"
    assert result["error"]["is_retryable"] is False
