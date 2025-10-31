import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import AnalyzeCatalogQuestionTool


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    return Mock()


@pytest.fixture
def analyze_catalog_question_tool(mock_api):
    """Creates an AnalyzeCatalogQuestionTool with mock API."""
    return AnalyzeCatalogQuestionTool(mock_api)


def test_analyze_catalog_question_tool_initialization(
    analyze_catalog_question_tool, mock_api
):
    """Test that the AnalyzeCatalogQuestionTool initializes correctly."""
    assert analyze_catalog_question_tool.name == "analyze_catalog_question"
    assert "PRIMARY ENTRY POINT" in analyze_catalog_question_tool.description
    assert analyze_catalog_question_tool.api == mock_api


def test_analyze_catalog_question_tool_run_success(
    analyze_catalog_question_tool, mock_api
):
    """Test successful workflow generation."""
    question = "Find sales tables in marketing domain"

    # Mock the expected response
    mock_response = f"""CATALOG QUESTION ANALYSIS WORKFLOW

Question: {question}

This is a comprehensive workflow for analyzing catalog questions.
Provides step-by-step guidance on handling complex data catalog queries.
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.analyze_catalog_question_stream.return_value = mock_generator()

    mock_api.enable_streaming = False

    result = analyze_catalog_question_tool.run(question=question)

    # Verify API was called correctly
    mock_api.analyze_catalog_question_stream.assert_called_once_with(
        question=question, chat_id=None
    )

    # Verify result is a string
    assert isinstance(result, str)

    # Verify question is embedded in the workflow
    assert question in result

    # Verify workflow header
    assert "CATALOG QUESTION ANALYSIS WORKFLOW" in result
