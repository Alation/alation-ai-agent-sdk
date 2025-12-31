import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.tools import GenerateDataProductTool
from alation_ai_agent_sdk.api import AlationAPIError


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    api = Mock()
    api.enable_streaming = False
    api.base_url = "https://test.alation.com"
    return api


@pytest.fixture
def generate_data_product_tool(mock_api):
    """Creates a GenerateDataProductTool with mock API."""
    return GenerateDataProductTool(mock_api)


def test_generate_data_product_tool_initialization(generate_data_product_tool, mock_api):
    """Test that the GenerateDataProductTool initializes correctly."""
    assert generate_data_product_tool.name == "generate_data_product"
    assert "Alation Data Product" in generate_data_product_tool.description
    assert generate_data_product_tool.api == mock_api


def test_generate_data_product_tool_run(generate_data_product_tool, mock_api):
    """Test that the tool returns the complete instruction set."""
    # Mock response from backend with complete instructions
    mock_response = """
You are a highly specialized AI assistant for Alation. Your mission is to CONVERT user-provided information into a valid Alation Data Product YAML file.

**--- THE SCHEMA ---**
type: object
title: Data Product Schema
properties:
  product:
    type: object
    properties:
      productId:
        type: string
      version:
        type: string
      deliverySystems:
        type: object

**--- THE EXAMPLE ---**
product:
  productId: "marketing.db.customer_360_view"
  version: "1.0"
  deliverySystems:
    snowflake_prod:
      type: sql
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.generate_data_product_stream.return_value = mock_generator()

    result = generate_data_product_tool.run()

    # Verify API was called
    mock_api.generate_data_product_stream.assert_called_once_with(chat_id=None)

    # Verify the result is a string
    assert isinstance(result, str)

    # Verify key components are present in the instructions
    assert "Alation Data Product" in result or "Data Product" in result
    assert "deliverySystems" in result
    assert "productId" in result


def test_generate_data_product_tool_run_api_error(generate_data_product_tool, mock_api):
    """Test handling of API errors."""
    # Mock API error
    api_error = AlationAPIError(
        message="Failed to fetch data product schema",
        status_code=500,
        reason="Schema Fetch Failed",
        resolution_hint="Ensure your Alation instance is accessible",
    )
    mock_api.generate_data_product_stream.side_effect = api_error

    result = generate_data_product_tool.run()

    # Verify API was called
    mock_api.generate_data_product_stream.assert_called_once_with(chat_id=None)

    # Verify error is returned
    assert "error" in result
    assert result["error"]["message"] == "Failed to fetch data product schema"
    assert result["error"]["reason"] == "Schema Fetch Failed"


def test_generate_data_product_tool_content_validation(generate_data_product_tool, mock_api):
    """Test that the generated content follows expected patterns."""
    # Mock response with expected patterns
    mock_response = """
You are a highly specialized AI assistant for Alation.

**CORE DIRECTIVES:**
1. ZERO HALLUCINATION & INVENTION
2. STRICT SCHEMA ADHERENCE
3. DATA CLEANING & FORMATTING

**THE SCHEMA:**
type: object
properties:
  product:
    type: object
    properties:
      productId:
        type: string
      contactEmail:
        type: string

**THE EXAMPLE:**
product:
  productId: "test.product"
  version: "1.0"
"""

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.generate_data_product_stream.return_value = mock_generator()

    result = generate_data_product_tool.run()

    # Verify API was called
    mock_api.generate_data_product_stream.assert_called_once_with(chat_id=None)

    # Verify the result is a string
    assert isinstance(result, str)

    # Verify critical instructions are present
    assert "HALLUCINATION" in result
    assert "EXAMPLE" in result or "THE EXAMPLE" in result
    assert "THE SCHEMA" in result or "SCHEMA" in result
    assert "productId" in result
    assert "contactEmail" in result
