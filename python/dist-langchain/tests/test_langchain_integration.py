import pytest
from unittest.mock import Mock, MagicMock

from langchain.tools import StructuredTool
from alation_ai_agent_langchain import get_langchain_tools
from alation_ai_agent_sdk import AlationAIAgentSDK

@pytest.fixture
def mock_sdk_with_context_tool():
    """
    Creates a mock AlationAIAgentSDK with a mock context_tool.
    This mock SDK will be passed to get_langchain_tools.
    """
    mock_sdk = Mock(spec=AlationAIAgentSDK if 'AlationAIAgentSDK' in globals() else object)

    mock_sdk.context_tool = MagicMock()
    mock_sdk.context_tool.name = "AlationContextToolFromSDK"
    mock_sdk.context_tool.description = "Provides context from Alation. Sourced from SDK's context_tool."
    mock_sdk.context_tool.run = MagicMock(return_value="Expected context data via SDK run")
    # Add mock for data_product_tool to support new toolkit
    mock_sdk.data_product_tool = MagicMock()
    mock_sdk.data_product_tool.name = "AlationDataProductsToolFromSDK"
    mock_sdk.data_product_tool.description = "Provides data products from Alation. Sourced from SDK's data_product_tool."
    mock_sdk.data_product_tool.run = MagicMock(return_value="Expected data products via SDK run")
    # Patch .run for StructuredTool.func compatibility
    def run_with_signature(*args, **kwargs):
        return mock_sdk.context_tool.run(*args, **kwargs)
    def run_with_query_or_product_id(*args, **kwargs):
        return mock_sdk.data_product_tool.run(*args, **kwargs)
    mock_sdk.context_tool.run_with_signature = run_with_signature
    mock_sdk.data_product_tool.run_with_query_or_product_id = run_with_query_or_product_id
    return mock_sdk


def test_get_langchain_tools_returns_list_with_alation_tool(mock_sdk_with_context_tool):
    """
    Tests that get_langchain_tools returns a list containing the Alation context tool
    which should be an instance of StructuredTool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)

    assert isinstance(tools_list, list), "get_langchain_tools should return a list."
    assert len(tools_list) > 0, "The returned list of tools should not be empty."

    alation_tool = tools_list[0]
    assert isinstance(alation_tool, StructuredTool), \
        "The Alation tool in the list should be an instance of StructuredTool."


def test_alation_tool_properties_from_list(mock_sdk_with_context_tool):
    """
    Tests that the Alation StructuredTool obtained from get_langchain_tools
    has the correct name and description, derived from the SDK's context_tool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool = tools_list[0] # Assuming it's the first tool

    assert alation_tool.name == mock_sdk_with_context_tool.context_tool.name, \
        "Tool name should match the name from the SDK's context_tool."
    assert alation_tool.description == mock_sdk_with_context_tool.context_tool.description, \
        "Tool description should match the description from the SDK's context_tool."


def test_alation_tool_run_invokes_sdk_context_tool_no_signature(mock_sdk_with_context_tool):
    """
    Tests that the Alation tool's function (derived from sdk.context_tool.run)
    is called correctly when no signature is provided.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool = tools_list[0]

    test_question = "What are the active data sources?"
    expected_result = "Expected context data via SDK run" # From mock_sdk_with_context_tool setup

    actual_result = alation_tool.func(question=test_question, signature=None)

    mock_sdk_with_context_tool.context_tool.run.assert_called_once_with(test_question, None)

    assert actual_result == expected_result, \
        "The tool's function should return the result from the SDK's context_tool.run."


def test_alation_tool_run_invokes_sdk_context_tool_with_signature(mock_sdk_with_context_tool):
    """
    Tests that the Alation tool's function is called correctly when a signature is provided.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool = tools_list[0]

    test_question = "Describe tables related to 'customers'."
    test_signature = {"table": {"fields_required": ["name", "description", "steward"]}}
    expected_result = "Expected context data via SDK run" # From mock_sdk_with_context_tool setup

    actual_result = alation_tool.func(question=test_question, signature=test_signature)

    mock_sdk_with_context_tool.context_tool.run.assert_called_once_with(test_question, test_signature)
    assert actual_result == expected_result, \
        "The tool's function should return the result from SDK's context_tool.run when a signature is provided."


def test_alation_tool_func_can_be_called_multiple_times(mock_sdk_with_context_tool):
    """
    Tests that the tool's func can be called multiple times, and each call is
    delegated to the underlying sdk.context_tool.run correctly.
    This also implicitly tests the 'run_with_signature' wrapper logic within the tool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool_function = tools_list[0].func # Get the callable function from the tool

    question1 = "First question?"
    signature1 = {"detail_level": "summary"}
    question2 = "Second question, no signature."

    # First call with signature
    alation_tool_function(question=question1, signature=signature1)
    mock_sdk_with_context_tool.context_tool.run.assert_called_with(question1, signature1)

    # Second call without signature
    alation_tool_function(question=question2, signature=None)
    mock_sdk_with_context_tool.context_tool.run.assert_called_with(question2, None)

    # Verify total calls to the mock
    assert mock_sdk_with_context_tool.context_tool.run.call_count == 2, \
        "SDK's context_tool.run should have been called twice."

