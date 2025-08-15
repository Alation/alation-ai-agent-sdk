import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import GetCustomFieldsDefinitionsTool
from alation_ai_agent_sdk.api import AlationAPIError


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def get_custom_field_definitions_tool(mock_api):
    """Creates a GetCustomFieldDefinitionsTool with mock API."""
    return GetCustomFieldsDefinitionsTool(mock_api)


def test_get_custom_field_definitions_tool_run_success(get_custom_field_definitions_tool, mock_api):
    """Test successful custom field definitions retrieval."""
    mock_response = [
        {
            "id": 10001,
            "name_singular": "Data Classification",
            "field_type": "PICKER",
            "allowed_otypes": ["table", "attribute"],
            "options": ["Public", "Internal", "Confidential"],
            "tooltip_text": "Classification level for data",
            "allow_multiple": False,
            "name_plural": "Data Classifications",
            "extra_field": "should_be_filtered"
        },
        {
            "id": 10002,
            "name_singular": "Business Owner",
            "field_type": "TEXT",
            "allowed_otypes": None,
            "options": None,
            "tooltip_text": None,
            "allow_multiple": False,
            "name_plural": ""
        }
    ]
    mock_api.get_custom_fields.return_value = mock_response

    result = get_custom_field_definitions_tool.run()

    # Verify API was called correctly
    mock_api.get_custom_fields.assert_called_once()

    # Verify result structure
    assert "custom_fields" in result
    assert "usage_guide" in result
    assert len(result["custom_fields"]) == 2

    # Verify field filtering worked
    first_field = result["custom_fields"][0]
    assert first_field["id"] == 10001
    assert first_field["name_singular"] == "Data Classification"
    assert "extra_field" not in first_field


def test_get_custom_field_definitions_tool_run_403_returns_builtin_fields(get_custom_field_definitions_tool, mock_api):
    """Test handling of 403 errors - should return built-in fields."""
    # Mock 403 API error
    api_error = AlationAPIError(
        message="Forbidden",
        status_code=403,
        reason="Forbidden",
        resolution_hint="Admin permissions required"
    )
    mock_api.get_custom_fields.side_effect = api_error

    result = get_custom_field_definitions_tool.run()

    # Verify API was called
    mock_api.get_custom_fields.assert_called_once()

    # Verify built-in fields are returned instead of error
    assert "custom_fields" in result
    assert "usage_guide" in result
    assert "message" in result
    assert "Admin permissions required" in result["message"]

    # Verify built-in fields are present
    assert len(result["custom_fields"]) == 3  # title, description, steward
    field_ids = [field["id"] for field in result["custom_fields"]]
    assert 3 in field_ids  # title
    assert 4 in field_ids  # description
    assert 8 in field_ids  # steward


def test_get_custom_field_definitions_tool_run_non_403_api_error(get_custom_field_definitions_tool, mock_api):
    """Test handling of non-403 API errors - should return error."""
    # Mock non-403 API error
    api_error = AlationAPIError(
        message="Internal Server Error",
        status_code=500,
        reason="Internal Server Error",
        resolution_hint="Server error occurred"
    )
    mock_api.get_custom_fields.side_effect = api_error

    result = get_custom_field_definitions_tool.run()

    # Verify API was called
    mock_api.get_custom_fields.assert_called_once()

    # Verify error is returned for non-403 errors
    assert "error" in result
    assert result["error"]["message"] == "Internal Server Error"
    assert result["error"]["status_code"] == 500
    assert result["error"]["reason"] == "Internal Server Error"


def test_get_custom_field_definitions_tool_run_empty_response(get_custom_field_definitions_tool, mock_api):
    """Test handling of empty custom fields response."""
    mock_api.get_custom_fields.return_value = []

    result = get_custom_field_definitions_tool.run()

    # Verify result
    assert "custom_fields" in result
    assert len(result["custom_fields"]) == 0
    assert "usage_guide" in result
