from alation_ai_agent_sdk.sdk import AlationTools
from alation_ai_agent_sdk.utils import is_tool_enabled
import pytest
from unittest.mock import Mock, MagicMock

from langchain.tools import StructuredTool
from alation_ai_agent_langchain import UserAccountAuthParams, get_langchain_tools
from alation_ai_agent_sdk import AlationAIAgentSDK


def get_sdk_mock():
    mock_sdk = Mock(
        spec=AlationAIAgentSDK if "AlationAIAgentSDK" in globals() else object
    )

    # Add the required attributes for tool enablement logic
    mock_sdk.disabled_tools = set()
    mock_sdk.enabled_beta_tools = set()

    mock_sdk.context_tool = MagicMock()
    mock_sdk.context_tool.name = "AlationContextToolFromSDK"
    mock_sdk.context_tool.description = (
        "Provides context from Alation. Sourced from SDK's context_tool."
    )
    mock_sdk.context_tool.run = MagicMock(
        return_value="Expected context data via SDK run"
    )
    # Add check_data_quality_tool mock to avoid AttributeError in tool.py
    mock_sdk.check_data_quality_tool = MagicMock()
    mock_sdk.check_data_quality_tool.name = "CheckDataQualityToolFromSDK"
    mock_sdk.check_data_quality_tool.description = (
        "Checks data quality via SDK's check_data_quality_tool."
    )
    mock_sdk.check_data_quality_tool.run = MagicMock(
        return_value="Expected data quality result"
    )
    # Add mock for data_product_tool to support new toolkit
    mock_sdk.data_product_tool = MagicMock()
    mock_sdk.data_product_tool.name = "AlationDataProductsToolFromSDK"
    mock_sdk.data_product_tool.description = (
        "Provides data products from Alation. Sourced from SDK's data_product_tool."
    )
    mock_sdk.data_product_tool.run = MagicMock(
        return_value="Expected data products via SDK run"
    )
    # Add mock for AlationBulkRetrievalTool
    mock_sdk.bulk_retrieval_tool = MagicMock()
    mock_sdk.bulk_retrieval_tool.name = "AlationBulkRetrievalToolFromSDK"
    mock_sdk.bulk_retrieval_tool.description = (
        "Provides bulk retrieval from Alation. Sourced from SDK's bulk_retrieval."
    )
    mock_sdk.bulk_retrieval_tool.run = MagicMock(
        return_value="Expected bulk retrieval data via SDK run"
    )
    # Add mock for update_catalog_asset_metadata_tool
    mock_sdk.update_catalog_asset_metadata_tool = MagicMock()
    mock_sdk.update_catalog_asset_metadata_tool.name = (
        "UpdateCatalogAssetMetadataToolFromSDK"
    )
    mock_sdk.update_catalog_asset_metadata_tool.description = (
        "Updates catalog asset metadata via SDK's update_catalog_asset_metadata_tool."
    )
    mock_sdk.update_catalog_asset_metadata_tool.run = MagicMock(
        return_value="Expected update catalog asset metadata via SDK run"
    )
    # Add mock for check_job_status_tool
    mock_sdk.check_job_status_tool = MagicMock()
    mock_sdk.check_job_status_tool.name = "CheckJobStatusToolFromSDK"
    mock_sdk.check_job_status_tool.description = (
        "Checks job status via SDK's check_job_status_tool."
    )
    mock_sdk.check_job_status_tool.run = MagicMock(
        return_value="Expected check job status via SDK run"
    )
    # Add mock for generate data product
    mock_sdk.generate_data_product_tool = MagicMock()
    mock_sdk.generate_data_product_tool.name = "GenerateDataProductToolFromSDK"
    mock_sdk.generate_data_product_tool.description = (
        "Generates data product schemas from SDK's generate_data_product_tool."
    )

    mock_sdk.lineage_tool = MagicMock()
    mock_sdk.lineage_tool.name = "GetLineageToolFromSDK"
    mock_sdk.lineage_tool.description = "Provides lineage from SDK"

    mock_sdk.get_custom_fields_definitions_tool = MagicMock()
    mock_sdk.get_custom_fields_definitions_tool.name = "get_custom_fields_definitions"
    mock_sdk.get_custom_fields_definitions_tool.description = (
        "Gets custom field definitions"
    )

    mock_sdk.get_data_dictionary_instructions_tool = MagicMock()
    mock_sdk.get_data_dictionary_instructions_tool.name = (
        "get_data_dictionary_instructions"
    )
    mock_sdk.get_data_dictionary_instructions_tool.description = (
        "Gets data dictionary instructions"
    )

    # Patch .run for StructuredTool.func compatibility
    def run_with_signature(*args, **kwargs):
        return mock_sdk.context_tool.run(*args, **kwargs)

    def run_with_query_or_product_id(*args, **kwargs):
        return mock_sdk.data_product_tool.run(*args, **kwargs)

    def run_with_bulk_signature(*args, **kwargs):
        return mock_sdk.bulk_retrieval_tool.run(*args, **kwargs)

    def run_with_lineage_tool(*args, **kwargs):
        return mock_sdk.lineage_tool.run(*args, **kwargs)

    mock_sdk.context_tool.run_with_signature = run_with_signature
    mock_sdk.data_product_tool.run_with_query_or_product_id = (
        run_with_query_or_product_id
    )
    mock_sdk.bulk_retrieval_tool.run_with_bulk_signature = run_with_bulk_signature
    mock_sdk.lineage_tool.run_with_lineage_tool = run_with_lineage_tool
    return mock_sdk


@pytest.fixture
def mock_sdk_with_context_tool():
    """
    Creates a mock AlationAIAgentSDK with a mock context_tool.
    This mock SDK will be passed to get_langchain_tools.
    """
    return get_sdk_mock()


def test_get_langchain_tools_returns_list_with_alation_tool(mock_sdk_with_context_tool):
    """
    Tests that get_langchain_tools returns a list containing the Alation context tool
    which should be an instance of StructuredTool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)

    assert isinstance(tools_list, list), "get_langchain_tools should return a list."
    assert len(tools_list) > 0, "The returned list of tools should not be empty."

    alation_tool = tools_list[0]
    assert isinstance(
        alation_tool, StructuredTool
    ), "The Alation tool in the list should be an instance of StructuredTool."


def test_get_langchain_tools_skips_beta_tools_by_default():
    sdk = AlationAIAgentSDK(
        base_url="https://api.alation.com",
        auth_method="user_account",
        auth_params=UserAccountAuthParams(
            user_id=1,
            refresh_token="blah",
        ),
        skip_instance_info=True,  # No need to fetch for this test
    )
    assert len(sdk.enabled_beta_tools) == 0
    assert (
        is_tool_enabled(
            AlationTools.LINEAGE, sdk.disabled_tools, sdk.enabled_beta_tools
        )
        is False
    )

    tools_list = get_langchain_tools(sdk)
    assert all(
        t.name != AlationTools.LINEAGE for t in tools_list
    ), "Beta tools should be skipped."


def test_get_langchain_tools_skips_disabled_tools():
    sdk = AlationAIAgentSDK(
        base_url="https://api.alation.com",
        auth_method="user_account",
        auth_params=UserAccountAuthParams(
            user_id=1,
            refresh_token="blah",
        ),
        disabled_tools=set([AlationTools.AGGREGATED_CONTEXT]),
        skip_instance_info=True,  # No need to fetch for this test
    )
    assert len(sdk.disabled_tools) == 1
    assert (
        is_tool_enabled(
            AlationTools.AGGREGATED_CONTEXT, sdk.disabled_tools, sdk.enabled_beta_tools
        )
        is False
    )

    tools_list = get_langchain_tools(sdk)
    assert all(
        t.name != AlationTools.AGGREGATED_CONTEXT for t in tools_list
    ), "Disabled tools should be skipped."


def test_alation_tool_properties_from_list(mock_sdk_with_context_tool):
    """
    Tests that the Alation StructuredTool obtained from get_langchain_tools
    has the correct name and description, derived from the SDK's context_tool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    # Find the context tool by name
    alation_tool = next(
        t for t in tools_list if t.name == mock_sdk_with_context_tool.context_tool.name
    )

    assert (
        alation_tool.name == mock_sdk_with_context_tool.context_tool.name
    ), "Tool name should match the name from the SDK's context_tool."
    assert (
        alation_tool.description == mock_sdk_with_context_tool.context_tool.description
    ), "Tool description should match the description from the SDK's context_tool."


def test_alation_tool_run_invokes_sdk_context_tool_no_signature(
    mock_sdk_with_context_tool,
):
    """
    Tests that the Alation tool's function (derived from sdk.context_tool.run)
    is called correctly when no signature is provided.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool = next(
        t for t in tools_list if t.name == mock_sdk_with_context_tool.context_tool.name
    )

    test_question = "What are the active data sources?"
    expected_result = (
        "Expected context data via SDK run"  # From mock_sdk_with_context_tool setup
    )

    actual_result = alation_tool.func(question=test_question, signature=None)

    mock_sdk_with_context_tool.context_tool.run.assert_called_once_with(
        question=test_question, signature=None
    )

    assert (
        actual_result == expected_result
    ), "The tool's function should return the result from the SDK's context_tool.run."


def test_alation_tool_run_invokes_sdk_context_tool_with_signature(
    mock_sdk_with_context_tool,
):
    """
    Tests that the Alation tool's function is called correctly when a signature is provided.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool = next(
        t for t in tools_list if t.name == mock_sdk_with_context_tool.context_tool.name
    )

    test_question = "Describe tables related to 'customers'."
    test_signature = {"table": {"fields_required": ["name", "description", "steward"]}}
    expected_result = (
        "Expected context data via SDK run"  # From mock_sdk_with_context_tool setup
    )

    actual_result = alation_tool.func(question=test_question, signature=test_signature)

    mock_sdk_with_context_tool.context_tool.run.assert_called_once_with(
        question=test_question, signature=test_signature
    )
    assert (
        actual_result == expected_result
    ), "The tool's function should return the result from SDK's context_tool.run when a signature is provided."


def test_alation_tool_func_can_be_called_multiple_times(mock_sdk_with_context_tool):
    """
    Tests that the tool's func can be called multiple times, and each call is
    delegated to the underlying sdk.context_tool.run correctly.
    This also implicitly tests the 'run_with_signature' wrapper logic within the tool.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)
    assert len(tools_list) > 0, "Tool list should not be empty."
    alation_tool_function = next(
        t for t in tools_list if t.name == mock_sdk_with_context_tool.context_tool.name
    ).func

    question1 = "First question?"
    signature1 = {"detail_level": "summary"}
    question2 = "Second question, no signature."

    # First call with signature
    alation_tool_function(question=question1, signature=signature1)
    mock_sdk_with_context_tool.context_tool.run.assert_called_with(
        question=question1, signature=signature1
    )

    # Second call without signature
    alation_tool_function(question=question2, signature=None)
    mock_sdk_with_context_tool.context_tool.run.assert_called_with(
        question=question2, signature=None
    )

    # Verify total calls to the mock
    assert (
        mock_sdk_with_context_tool.context_tool.run.call_count == 2
    ), "SDK's context_tool.run should have been called twice."
