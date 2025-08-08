import pytest
import time
from unittest.mock import Mock, patch
from alation_ai_agent_sdk.tools import GenerateDataProductTool
from alation_ai_agent_sdk.api import AlationAPIError
from alation_ai_agent_sdk.data_product import get_schema_content


def test_generate_data_product_tool_initialization():
    """Test that the GenerateDataProductTool requires an API instance."""
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"
    tool = GenerateDataProductTool(mock_api)
    assert tool.name == "generate_data_product"
    assert "Alation Data Product" in tool.description
    assert tool.api == mock_api


def test_generate_data_product_tool_run():
    """Test that the tool returns the complete instruction set."""
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    # Mock successful schema fetch
    mock_schema_content = "type: object\ntitle: Test Schema"
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = mock_schema_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = GenerateDataProductTool(mock_api)
        result = tool.run()

        # Verify the result is a string
        assert isinstance(result, str)

        # Verify key components are present in the instructions
        assert "Alation Data Product" in result
        assert "deliverySystems" in result
        assert "productId" in result

        # Verify the dynamic schema was fetched
        mock_get.assert_called_once_with(
            "https://test.alation.com/static/swagger/specs/data_products/product_schema.yaml",
            timeout=10,
        )


def test_generate_data_product_tool_run_with_fetch_failure():
    """Test that the tool raises an error when fetch fails (no fallback)."""
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    # Mock failed schema fetch
    with patch("requests.get", side_effect=Exception("Network error")):
        tool = GenerateDataProductTool(mock_api)

        # Should raise AlationAPIError when fetch fails
        with pytest.raises(AlationAPIError) as exc_info:
            tool.run()

        assert "Failed to fetch data product schema" in str(exc_info.value)
        assert exc_info.value.reason == "Schema Fetch Failed"


def test_generate_data_product_tool_fetch_schema_success():
    """Test successful schema fetching from instance."""
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    mock_schema_content = """
type: object  
title: Dynamic Schema
properties:
  product:
    type: object
"""

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = mock_schema_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = GenerateDataProductTool(mock_api)

        result = get_schema_content(tool)

        assert result == mock_schema_content
        mock_get.assert_called_once_with(
            "https://test.alation.com/static/swagger/specs/data_products/product_schema.yaml",
            timeout=10,
        )


def test_generate_data_product_tool_content_validation():
    """Test that the generated content follows expected patterns."""
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    # Mock schema fetch to return a basic schema
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = (
            "type: object\ntitle: Test Schema\nproperties:\n  product:\n    type: object"
        )
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = GenerateDataProductTool(mock_api)
        result = tool.run()

        # Verify critical instructions are present
        required_phrases = [
            "HALLUCINATION",
            "EXAMPLE",
            "THE SCHEMA",
            "`productId`",
            "`contactEmail`",
        ]

        for phrase in required_phrases:
            assert phrase in result, f"Missing required phrase: {phrase}"

        # Verify schema content is included
        assert "Test Schema" in result


def test_cache_is_used_on_subsequent_calls():
    """
    Tests that the schema is fetched from the network only once and then served
    from the cache on subsequent calls.
    """
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = (
            "type: object\ntitle: Test Schema\nproperties:\n  product:\n    type: object"
        )
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = GenerateDataProductTool(mock_api)

        # First call should trigger the network request
        tool.run()

        # Second call should use the cache
        tool.run()

        # Verify that requests.get was only called once
        mock_get.assert_called_once()


def test_cache_expires_after_ttl():
    """
    Tests that the schema cache expires after the TTL and is re-fetched.
    """
    mock_api = Mock()
    mock_api.base_url = "https://test.alation.com"

    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = (
            "type: object\ntitle: Test Schema\nproperties:\n  product:\n    type: object"
        )
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = GenerateDataProductTool(mock_api)
        # very short TTL for testing
        tool.CACHE_TTL_SECONDS = 0.1

        # First call should trigger a network request and populate the cache
        tool.run()

        # Wait for the cache to expire
        time.sleep(0.2)

        # Second call should trigger another network request
        tool.run()

        # Verify that requests.get was called twice
        assert mock_get.call_count == 2
