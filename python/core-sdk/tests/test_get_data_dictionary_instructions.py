import pytest
import time
from unittest.mock import Mock, patch
from alation_ai_agent_sdk.tools import GetDataDictionaryInstructionsTool
from alation_ai_agent_sdk.api import AlationAPIError


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def get_data_dictionary_instructions_tool(mock_api):
    """Creates a GetDataDictionaryInstructionsTool with mock API."""
    return GetDataDictionaryInstructionsTool(mock_api)


def test_get_data_dictionary_instructions_tool_initialization(get_data_dictionary_instructions_tool, mock_api):
    """Test that the GetDataDictionaryInstructionsTool initializes correctly."""
    assert get_data_dictionary_instructions_tool.name == "get_data_dictionary_instructions"
    assert "CSV" in get_data_dictionary_instructions_tool.description
    assert get_data_dictionary_instructions_tool.api == mock_api


def test_get_data_dictionary_instructions_tool_run_success_with_custom_fields(get_data_dictionary_instructions_tool, mock_api):
    """Test successful instruction generation with custom fields."""
    # Mock custom fields response
    mock_custom_fields = [
        {
            "id": 10001,
            "name_singular": "Data Classification",
            "field_type": "PICKER",
            "allowed_otypes": ["table"],
            "options": ["Public", "Internal", "Confidential"],
            "tooltip_text": "Data classification level",
            "allow_multiple": False,
            "name_plural": "Data Classifications"
        }
    ]
    mock_api.get_custom_fields.return_value = mock_custom_fields

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_custom_fields.assert_called_once()

    # Verify result
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "HIERARCHY GROUPING RULES" in result
    assert "CSV FORMAT & HEADERS" in result
    assert "Data Classification" in result
    assert "10001" in result


def test_get_data_dictionary_instructions_tool_run_success_without_custom_fields(get_data_dictionary_instructions_tool, mock_api):
    """Test instruction generation when custom fields returns 403 (non-admin user)."""
    # Mock 403 error for custom fields
    api_error = AlationAPIError(
        message="Forbidden",
        status_code=403,
        reason="Forbidden"
    )
    mock_api.get_custom_fields.side_effect = api_error

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_custom_fields.assert_called_once()

    # Verify result is still valid instructions
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "Built-in Fields" in result
    assert "3|title" in result
    assert "4|description" in result


def test_get_data_dictionary_instructions_tool_run_empty_custom_fields(get_data_dictionary_instructions_tool, mock_api):
    """Test instruction generation with empty custom fields."""
    mock_api.get_custom_fields.return_value = []

    result = get_data_dictionary_instructions_tool.run()

    # Verify result
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "No custom fields available" in result
