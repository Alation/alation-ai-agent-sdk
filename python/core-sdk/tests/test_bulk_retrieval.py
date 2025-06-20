import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import AlationBulkRetrievalTool
from alation_ai_agent_sdk.api import AlationAPIError


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def bulk_retrieval_tool(mock_api):
    """Creates an AlationBulkRetrievalTool with mock API."""
    return AlationBulkRetrievalTool(mock_api)


def test_bulk_retrieval_tool_run_success(bulk_retrieval_tool, mock_api):
    """Test successful bulk retrieval."""
    # Mock response
    mock_response = {
        "relevant_tables": [
            {
                "name": "customers",
                "description": "Customer data",
                "url": "https://alation.com/table/123"
            }
        ]
    }
    mock_api.get_bulk_objects_from_catalog.return_value = mock_response

    signature = {
        "table": {
            "fields_required": ["name", "description", "url"],
            "limit": 1
        }
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
        resolution_hint="Check signature format"
    )
    mock_api.get_bulk_objects_from_catalog.side_effect = api_error

    invalid_signature = {
        "unknown": {
            "fields_required": ["name"],
            "limit": 100
        }
    }

    result = bulk_retrieval_tool.run(invalid_signature)

    # Verify API was called
    mock_api.get_bulk_objects_from_catalog.assert_called_once_with(invalid_signature)

    # Verify error handling
    assert "error" in result
    assert result["error"]["message"] == "Bad Request"
    assert result["error"]["status_code"] == 400
    assert result["error"]["reason"] == "Bad Request"
