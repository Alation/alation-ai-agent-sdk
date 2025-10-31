import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import SignatureCreationTool


@pytest.fixture
def mock_api():
    api = Mock()
    api.enable_streaming = False
    """Creates a mock AlationAPI for testing."""
    return api


@pytest.fixture
def signature_creation_tool(mock_api):
    """Creates a SignatureCreationTool with mock API."""
    return SignatureCreationTool(mock_api)


def test_signature_creation_tool_initialization(signature_creation_tool, mock_api):
    """Test that the SignatureCreationTool initializes correctly."""
    assert signature_creation_tool.name == "get_signature_creation_instructions"
    assert "signature" in signature_creation_tool.description.lower()
    assert signature_creation_tool.api == mock_api


def test_signature_creation_tool_run_success(signature_creation_tool, mock_api):
    """Test successful instruction generation."""

    # Mock the expected response (comprehensive guide with detailed content)
    mock_response = """ALATION SIGNATURE CREATION GUIDE

    This comprehensive guide covers creating signatures for catalog searches and bulk retrieval operations.

    OBJECT TYPES:
    - table: Database tables and views
    - column: Table columns and attributes
    - schema: Database schemas and namespaces
    - query: SQL queries and stored procedures
    - documentation: Documentation objects and articles
    - bi_report: Business Intelligence reports and dashboards

    SIGNATURE STRUCTURE:
    - fields_required: List of required fields to return in results
    - search_filters: Filtering criteria to apply to search results
    - child_objects: Nested object specifications for hierarchical data
    - limit: Maximum number of results to return (default varies by object type)

    SUPPORTED FILTERS BY OBJECT TYPE:
    Table filters:
    - endorsement: Filter by endorsement status
    - steward: Filter by data steward assignments
    - schema_id: Filter by parent schema identifier
    - data_source_id: Filter by data source identifier

    Column filters:
    - data_type: Filter by column data type
    - is_primary_key: Filter by primary key status
    - is_foreign_key: Filter by foreign key status
    - table_id: Filter by parent table identifier

    REFERENCE SECTIONS:
    - supported_filters_by_object_type: Complete listing of available filters per object type
    - available_fields: Comprehensive field listing with descriptions and data types
    - filter_usage_guide: Usage examples, patterns, and best practices for effective filtering

    EXAMPLES:
    Basic table signature:
    {
        "table": {
            "fields_required": ["name", "title", "description", "url"],
            "limit": 10
        }
    }

    Advanced filtering example:
    {
        "table": {
            "fields_required": ["name", "title", "description", "steward", "url"],
            "search_filters": {
                "endorsement": ["Endorsed"],
                "data_source_id": [5, 10, 15]
            },
            "limit": 50
        }
    }
    """

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.get_signature_creation_instructions_stream.return_value = mock_generator()

    instructions = signature_creation_tool.run()

    # Verify API was called correctly
    mock_api.get_signature_creation_instructions_stream.assert_called_once()

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
