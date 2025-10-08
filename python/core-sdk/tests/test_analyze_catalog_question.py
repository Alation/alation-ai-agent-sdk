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
        analyze_catalog_question_tool,
):
    """Test successful workflow generation."""
    question = "Find sales tables in marketing domain"
    result = analyze_catalog_question_tool.run(question=question)

    # Verify result is a string
    assert isinstance(result, str)

    # Verify question is embedded in the workflow
    assert question in result

    # Verify workflow header
    assert "CATALOG QUESTION ANALYSIS WORKFLOW" in result
