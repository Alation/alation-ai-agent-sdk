from alation_ai_agent_sdk.sdk import AlationTools
from alation_ai_agent_sdk.utils import is_tool_enabled
import pytest
from unittest.mock import Mock, MagicMock

from langchain.tools import StructuredTool
from alation_ai_agent_langchain import get_langchain_tools
from alation_ai_agent_sdk import (
    AgentSDKOptions,
    AlationAIAgentSDK,
    ServiceAccountAuthParams,
)


def get_sdk_mock():
    mock_sdk = Mock(
        spec=AlationAIAgentSDK if "AlationAIAgentSDK" in globals() else object
    )

    # Add the required attributes for tool enablement logic
    mock_sdk.enabled_tools = set()
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

    mock_sdk.signature_creation_tool = MagicMock()
    mock_sdk.signature_creation_tool.name = "get_signature_creation_instructions"
    mock_sdk.signature_creation_tool.description = (
        "Gets signature creation instructions"
    )

    mock_sdk.analyze_catalog_question_tool = MagicMock()
    mock_sdk.analyze_catalog_question_tool.name = "analyze_catalog_question"
    mock_sdk.analyze_catalog_question_tool.description = (
        "Analyze catalog question and orchestrate"
    )

    # Add all the missing tools that are now required by the toolkit
    mock_sdk.bi_report_search_tool = MagicMock()
    mock_sdk.bi_report_search_tool.name = "bi_report_search"
    mock_sdk.bi_report_search_tool.description = "Search BI reports"

    mock_sdk.bi_report_agent_tool = MagicMock()
    mock_sdk.bi_report_agent_tool.name = "bi_report_agent"
    mock_sdk.bi_report_agent_tool.description = "BI Report Agent"

    mock_sdk.catalog_context_search_agent_tool = MagicMock()
    mock_sdk.catalog_context_search_agent_tool.name = "catalog_context_search_agent"
    mock_sdk.catalog_context_search_agent_tool.description = (
        "Catalog Context Search Agent"
    )

    mock_sdk.catalog_search_agent_tool = MagicMock()
    mock_sdk.catalog_search_agent_tool.name = "catalog_search_agent"
    mock_sdk.catalog_search_agent_tool.description = "Catalog Search Agent"

    mock_sdk.chart_create_agent_tool = MagicMock()
    mock_sdk.chart_create_agent_tool.name = "chart_create_agent"
    mock_sdk.chart_create_agent_tool.description = "Chart Create Agent"

    mock_sdk.custom_agent_tool = MagicMock()
    mock_sdk.custom_agent_tool.name = "custom_agent"
    mock_sdk.custom_agent_tool.description = "Custom Agent"

    mock_sdk.data_product_query_agent_tool = MagicMock()
    mock_sdk.data_product_query_agent_tool.name = "data_product_query_agent"
    mock_sdk.data_product_query_agent_tool.description = "Data Product Query Agent"

    mock_sdk.deep_research_agent_tool = MagicMock()
    mock_sdk.deep_research_agent_tool.name = "deep_research_agent"
    mock_sdk.deep_research_agent_tool.description = "Deep Research Agent"

    mock_sdk.generate_chart_from_sql_and_code_tool = MagicMock()
    mock_sdk.generate_chart_from_sql_and_code_tool.name = (
        "generate_chart_from_sql_and_code"
    )
    mock_sdk.generate_chart_from_sql_and_code_tool.description = (
        "Generate Chart from SQL and Code"
    )

    mock_sdk.get_data_schema_tool = MagicMock()
    mock_sdk.get_data_schema_tool.name = "get_data_schema"
    mock_sdk.get_data_schema_tool.description = "Get Data Schema"

    mock_sdk.get_data_sources_tool = MagicMock()
    mock_sdk.get_data_sources_tool.name = "get_data_sources"
    mock_sdk.get_data_sources_tool.description = "Get Data Sources"

    mock_sdk.list_data_products_tool = MagicMock()
    mock_sdk.list_data_products_tool.name = "list_data_products"
    mock_sdk.list_data_products_tool.description = "List Data Products"

    mock_sdk.query_flow_agent_tool = MagicMock()
    mock_sdk.query_flow_agent_tool.name = "query_flow_agent"
    mock_sdk.query_flow_agent_tool.description = "Query Flow Agent"

    mock_sdk.search_catalog_tool = MagicMock()
    mock_sdk.search_catalog_tool.name = "search_catalog"
    mock_sdk.search_catalog_tool.description = "Search Catalog"

    mock_sdk.get_search_filter_fields_tool = MagicMock()
    mock_sdk.get_search_filter_fields_tool.name = "get_search_filter_fields"
    mock_sdk.get_search_filter_fields_tool.description = "Get Search Filter Fields"

    mock_sdk.get_search_filter_values_tool = MagicMock()
    mock_sdk.get_search_filter_values_tool.name = "get_search_filter_values"
    mock_sdk.get_search_filter_values_tool.description = "Get Search Filter Values"

    mock_sdk.sql_execution_tool = MagicMock()
    mock_sdk.sql_execution_tool.name = "sql_execution"
    mock_sdk.sql_execution_tool.description = "SQL Execution"

    mock_sdk.sql_query_agent_tool = MagicMock()
    mock_sdk.sql_query_agent_tool.name = "sql_query_agent"
    mock_sdk.sql_query_agent_tool.description = "SQL Query Agent"

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
    assert isinstance(alation_tool, StructuredTool), (
        "The Alation tool in the list should be an instance of StructuredTool."
    )


def test_get_langchain_tools_skips_beta_tools_by_default():
    sdk = AlationAIAgentSDK(
        base_url="https://api.alation.com",
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams(
            client_id="mock-client-id",
            client_secret="mock-client-secret",
        ),
        sdk_options=AgentSDKOptions(skip_instance_info=True),
    )
    assert len(sdk.enabled_beta_tools) == 0
    assert (
        is_tool_enabled(
            AlationTools.LINEAGE,
            sdk.enabled_tools,
            sdk.disabled_tools,
            sdk.enabled_beta_tools,
        )
        is False
    )

    tools_list = get_langchain_tools(sdk)
    assert all(t.name != AlationTools.LINEAGE for t in tools_list), (
        "Beta tools should be skipped."
    )


def test_get_langchain_tools_skips_disabled_tools():
    sdk = AlationAIAgentSDK(
        base_url="https://api.alation.com",
        auth_method="service_account",
        auth_params=ServiceAccountAuthParams(
            client_id="mock-client-id",
            client_secret="mock-client-secret",
        ),
        disabled_tools=set([AlationTools.AGGREGATED_CONTEXT]),
        sdk_options=AgentSDKOptions(
            skip_instance_info=True
        ),  # No need to fetch for this test
    )
    assert len(sdk.disabled_tools) == 1
    assert (
        is_tool_enabled(
            AlationTools.AGGREGATED_CONTEXT,
            sdk.enabled_tools,
            sdk.disabled_tools,
            sdk.enabled_beta_tools,
        )
        is False
    )

    tools_list = get_langchain_tools(sdk)
    assert all(t.name != AlationTools.AGGREGATED_CONTEXT for t in tools_list), (
        "Disabled tools should be skipped."
    )


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

    assert alation_tool.name == mock_sdk_with_context_tool.context_tool.name, (
        "Tool name should match the name from the SDK's context_tool."
    )
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
        question=test_question, signature=None, chat_id=None
    )

    assert actual_result == expected_result, (
        "The tool's function should return the result from the SDK's context_tool.run."
    )


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
        question=test_question, signature=test_signature, chat_id=None
    )
    assert actual_result == expected_result, (
        "The tool's function should return the result from SDK's context_tool.run when a signature is provided."
    )


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
        question=question1, signature=signature1, chat_id=None
    )

    # Second call without signature
    alation_tool_function(question=question2, signature=None)
    mock_sdk_with_context_tool.context_tool.run.assert_called_with(
        question=question2, signature=None, chat_id=None
    )

    # Verify total calls to the mock
    assert mock_sdk_with_context_tool.context_tool.run.call_count == 2, (
        "SDK's context_tool.run should have been called twice."
    )


def test_all_tools_are_properly_wrapped(mock_sdk_with_context_tool):
    """
    Tests that all available tools are properly wrapped as StructuredTools
    and have the expected properties and functionality.
    """
    tools_list = get_langchain_tools(mock_sdk_with_context_tool)

    # Verify we have tools
    assert len(tools_list) > 0, "Should have multiple tools available"

    # Verify all tools are StructuredTool instances
    for tool in tools_list:
        assert isinstance(tool, StructuredTool), (
            f"Tool {tool.name} should be a StructuredTool"
        )
        assert tool.name, "Tool should have a name"
        assert tool.description, f"Tool {tool.name} should have a description"
        assert callable(tool.func), f"Tool {tool.name} should have a callable func"


def test_bi_report_agent_tool_wrapper():
    """
    Test that the BI Report Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.bi_report_agent_tool.run.return_value = {
        "result": "test bi report agent response"
    }

    tools_list = get_langchain_tools(mock_sdk)
    bi_tool = next((t for t in tools_list if t.name == "bi_report_agent"), None)

    assert bi_tool is not None, "BI Report Agent tool should be in the tools list"
    assert bi_tool.name == "bi_report_agent"
    assert bi_tool.description == "BI Report Agent"

    # Test the tool function
    result = bi_tool.func(message="test message")
    mock_sdk.bi_report_agent_tool.run.assert_called_once_with(
        message="test message", chat_id=None
    )
    assert result == {"result": "test bi report agent response"}


def test_catalog_search_agent_tool_wrapper():
    """
    Test that the Catalog Search Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.catalog_search_agent_tool.run.return_value = {
        "results": ["catalog item 1", "catalog item 2"]
    }

    tools_list = get_langchain_tools(mock_sdk)
    catalog_tool = next(
        (t for t in tools_list if t.name == "catalog_search_agent"), None
    )

    assert catalog_tool is not None, (
        "Catalog Search Agent tool should be in the tools list"
    )
    assert catalog_tool.name == "catalog_search_agent"
    assert catalog_tool.description == "Catalog Search Agent"

    # Test the tool function
    result = catalog_tool.func(message="search query")
    mock_sdk.catalog_search_agent_tool.run.assert_called_once_with(
        message="search query", chat_id=None
    )
    assert result == {"results": ["catalog item 1", "catalog item 2"]}


def test_sql_execution_tool_wrapper():
    """
    Test that the SQL Execution tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.sql_execution_tool.run.return_value = {"rows": [{"id": 1, "name": "test"}]}

    tools_list = get_langchain_tools(mock_sdk)
    sql_tool = next((t for t in tools_list if t.name == "sql_execution"), None)

    assert sql_tool is not None, "SQL Execution tool should be in the tools list"
    assert sql_tool.name == "sql_execution"
    assert sql_tool.description == "SQL Execution"

    # Test the tool function with required parameters
    result = sql_tool.func(
        data_product_id="test-dp-123",
        sql="SELECT * FROM test_table",
        result_table_name="results",
    )
    mock_sdk.sql_execution_tool.run.assert_called_once_with(
        data_product_id="test-dp-123",
        sql="SELECT * FROM test_table",
        result_table_name="results",
        pre_exec_sql=None,
        auth_id=None,
        chat_id=None,
    )
    assert result == {"rows": [{"id": 1, "name": "test"}]}


def test_data_product_query_agent_tool_wrapper():
    """
    Test that the Data Product Query Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.data_product_query_agent_tool.run.return_value = {
        "query_result": "data product response"
    }

    tools_list = get_langchain_tools(mock_sdk)
    dp_tool = next(
        (t for t in tools_list if t.name == "data_product_query_agent"), None
    )

    assert dp_tool is not None, (
        "Data Product Query Agent tool should be in the tools list"
    )
    assert dp_tool.name == "data_product_query_agent"
    assert dp_tool.description == "Data Product Query Agent"

    # Test the tool function with required parameters
    result = dp_tool.func(message="test query", data_product_id="dp-456")
    mock_sdk.data_product_query_agent_tool.run.assert_called_once_with(
        message="test query",
        data_product_id="dp-456",
        auth_id=None,
        chat_id=None,
    )
    assert result == {"query_result": "data product response"}


def test_search_catalog_tool_wrapper():
    """
    Test that the Search Catalog tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.search_catalog_tool.run.return_value = {"objects": ["table1", "table2"]}

    tools_list = get_langchain_tools(mock_sdk)
    search_tool = next((t for t in tools_list if t.name == "search_catalog"), None)

    assert search_tool is not None, "Search Catalog tool should be in the tools list"
    assert search_tool.name == "search_catalog"
    assert search_tool.description == "Search Catalog"

    # Test the tool function
    result = search_tool.func(
        search_term="customer", object_types=["table"], filters={"steward": "john"}
    )
    mock_sdk.search_catalog_tool.run.assert_called_once_with(
        search_term="customer",
        object_types=["table"],
        filters={"steward": "john"},
        chat_id=None,
    )
    assert result == {"objects": ["table1", "table2"]}


def test_custom_agent_tool_wrapper():
    """
    Test that the Custom Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.custom_agent_tool.run.return_value = {"agent_response": "custom result"}

    tools_list = get_langchain_tools(mock_sdk)
    custom_tool = next((t for t in tools_list if t.name == "custom_agent"), None)

    assert custom_tool is not None, "Custom Agent tool should be in the tools list"
    assert custom_tool.name == "custom_agent"
    assert custom_tool.description == "Custom Agent"

    # Test the tool function
    test_payload = {"message": "test", "config": "value"}
    result = custom_tool.func(agent_config_id="config-123", payload=test_payload)
    mock_sdk.custom_agent_tool.run.assert_called_once_with(
        agent_config_id="config-123",
        payload=test_payload,
        chat_id=None,
    )
    assert result == {"agent_response": "custom result"}
