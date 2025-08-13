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


def test_get_custom_field_definitions_tool_run_api_error(get_custom_field_definitions_tool, mock_api):
    """Test handling of API errors."""
    # Mock API error
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

    # Verify error handling
    assert "error" in result
    assert result["error"]["message"] == "Forbidden"
    assert result["error"]["status_code"] == 403
    assert result["error"]["reason"] == "Forbidden"


def test_get_custom_field_definitions_tool_run_empty_response(get_custom_field_definitions_tool, mock_api):
    """Test handling of empty custom fields response."""
    mock_api.get_custom_fields.return_value = []

    result = get_custom_field_definitions_tool.run()

    # Verify result
    assert "custom_fields" in result
    assert len(result["custom_fields"]) == 0
    assert "usage_guide" in result
