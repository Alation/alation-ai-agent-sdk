import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import SignatureCreationTool


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def signature_creation_tool(mock_api):
    """Creates a SignatureCreationTool with mock API."""
    return SignatureCreationTool(mock_api)


def test_signature_creation_tool_initialization(
        signature_creation_tool, mock_api
):
    """Test that the SignatureCreationTool initializes correctly."""
    assert signature_creation_tool.name == "get_signature_creation_instructions"
    assert "signature" in signature_creation_tool.description.lower()
    assert signature_creation_tool.api == mock_api


def test_signature_creation_tool_run_success(
        signature_creation_tool,
):
    """Test successful instruction generation."""
    instructions = signature_creation_tool.run()

    # Verify result is a string
    assert isinstance(instructions, str)

    # Verify comprehensive content
    assert len(instructions) > 1000

    # Verify key header
    assert "ALATION SIGNATURE CREATION GUIDE" in instructions

    # Check for object types
    assert "table" in instructions
    assert "column" in instructions
    assert "schema" in instructions
    assert "query" in instructions
    assert "documentation" in instructions
    assert "bi_report" in instructions

    # Check for signature structure
    assert "fields_required" in instructions
    assert "search_filters" in instructions
    assert "child_objects" in instructions

    # Check for reference sections
    assert "supported_filters_by_object_type" in instructions
    assert "available_fields" in instructions
    assert "filter_usage_guide" in instructions





