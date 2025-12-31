import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import GetDataDictionaryInstructionsTool
from alation_ai_agent_sdk.api import AlationAPIError


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    api = Mock()
    api.enable_streaming = False
    return api


@pytest.fixture
def get_data_dictionary_instructions_tool(mock_api):
    """Creates a GetDataDictionaryInstructionsTool with mock API."""
    return GetDataDictionaryInstructionsTool(mock_api)


def test_get_data_dictionary_instructions_tool_initialization(
    get_data_dictionary_instructions_tool, mock_api
):
    """Test that the GetDataDictionaryInstructionsTool initializes correctly."""
    assert (
        get_data_dictionary_instructions_tool.name == "get_data_dictionary_instructions"
    )
    assert "CSV" in get_data_dictionary_instructions_tool.description
    assert get_data_dictionary_instructions_tool.api == mock_api


def test_get_data_dictionary_instructions_tool_run_success_with_custom_fields(
    get_data_dictionary_instructions_tool, mock_api
):
    """Test successful instruction generation with custom fields."""
    # Mock response from backend with custom fields included
    mock_response = """# Alation Data Dictionary CSV Generation Instructions

## QUICK REFERENCE

**TL;DR**:
1. Group objects by hierarchy → Create one CSV per hierarchy
2. Use format: `al_datadict_item_properties,<field_headers>`
3. Each row: `oid=<id>;otype=<type>,<field_values>`

## CSV FORMAT & HEADERS

### Custom Fields:
- **Data Classification** (PICKER): `10001|Data Classification`
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.get_data_dictionary_instructions_stream.return_value = mock_generator()

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_data_dictionary_instructions_stream.assert_called_once_with(chat_id=None)

    # Verify result
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "CSV FORMAT & HEADERS" in result
    assert "Data Classification" in result
    assert "10001" in result


def test_get_data_dictionary_instructions_tool_run_success_without_custom_fields(
    get_data_dictionary_instructions_tool, mock_api
):
    """Test instruction generation when backend returns only built-in fields (non-admin user)."""
    # Mock response from backend with only built-in fields
    mock_response = """# Alation Data Dictionary CSV Generation Instructions

## QUICK REFERENCE

**TL;DR**:
1. Group objects by hierarchy → Create one CSV per hierarchy

## CSV FORMAT & HEADERS

### Built-in Fields:
- **Title** (TEXT): `3|title`
- **Description** (RICH_TEXT): `4|description`
- **Steward** (OBJECT_SET): `8|steward:user`
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.get_data_dictionary_instructions_stream.return_value = mock_generator()

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_data_dictionary_instructions_stream.assert_called_once_with(chat_id=None)

    # Verify result is still valid instructions
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "Built-in Fields" in result
    assert "3|title" in result
    assert "4|description" in result


def test_get_data_dictionary_instructions_tool_run_empty_custom_fields(
    get_data_dictionary_instructions_tool, mock_api
):
    """Test instruction generation with no custom fields available."""
    # Mock response from backend with no custom fields
    mock_response = """# Alation Data Dictionary CSV Generation Instructions

## QUICK REFERENCE

**TL;DR**:
1. Group objects by hierarchy → Create one CSV per hierarchy

### Custom Fields
No custom fields available (requires admin permissions).
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.get_data_dictionary_instructions_stream.return_value = mock_generator()

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_data_dictionary_instructions_stream.assert_called_once_with(chat_id=None)

    # Verify result
    assert isinstance(result, str)
    assert "QUICK REFERENCE" in result
    assert "No custom fields available" in result


def test_get_data_dictionary_instructions_tool_run_api_error(
    get_data_dictionary_instructions_tool, mock_api
):
    """Test handling of API errors."""
    # Mock API error
    api_error = AlationAPIError(
        message="Internal Server Error",
        status_code=500,
        reason="Internal Server Error",
        resolution_hint="Server error occurred",
    )
    mock_api.get_data_dictionary_instructions_stream.side_effect = api_error

    result = get_data_dictionary_instructions_tool.run()

    # Verify API was called
    mock_api.get_data_dictionary_instructions_stream.assert_called_once_with(chat_id=None)

    # Verify error is returned
    assert "error" in result
    assert result["error"]["message"] == "Internal Server Error"
    assert result["error"]["status_code"] == 500
    assert result["error"]["reason"] == "Internal Server Error"
