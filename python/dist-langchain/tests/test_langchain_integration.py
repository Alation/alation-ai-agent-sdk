import pytest

from alation_ai_agent_sdk.sdk import AlationTools
from alation_ai_agent_sdk.utils import is_tool_enabled
from unittest.mock import Mock, MagicMock
from langchain_core.tools import StructuredTool
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

    mock_sdk.catalog_context_search_agent_tool = MagicMock()
    mock_sdk.catalog_context_search_agent_tool.name = "catalog_context_search_agent"
    mock_sdk.catalog_context_search_agent_tool.description = (
        "Catalog Context Search Agent"
    )

    mock_sdk.custom_agent_tool = MagicMock()
    mock_sdk.custom_agent_tool.name = "custom_agent"
    mock_sdk.custom_agent_tool.description = "Custom Agent"

    mock_sdk.get_data_sources_tool = MagicMock()
    mock_sdk.get_data_sources_tool.name = "get_data_sources"
    mock_sdk.get_data_sources_tool.description = "Get Data Sources"

    mock_sdk.query_flow_agent_tool = MagicMock()
    mock_sdk.query_flow_agent_tool.name = "query_flow_agent"
    mock_sdk.query_flow_agent_tool.description = "Query Flow Agent"

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


def test_analyze_catalog_question_tool_wrapper():
    """
    Test that the Analyze Catalog Question tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.analyze_catalog_question_tool.run.return_value = {"analysis": "test result"}

    tools_list = get_langchain_tools(mock_sdk)
    analyze_tool = next((t for t in tools_list if t.name == "analyze_catalog_question"), None)

    assert analyze_tool is not None, "Analyze Catalog Question tool should be in the tools list"
    assert analyze_tool.name == "analyze_catalog_question"
    assert analyze_tool.description == "Analyze catalog question and orchestrate"

    # Test the tool function
    result = analyze_tool.func(question="What tables are available?")
    mock_sdk.analyze_catalog_question_tool.run.assert_called_once_with(
        question="What tables are available?", chat_id=None
    )
    assert result == {"analysis": "test result"}


def test_bulk_retrieval_tool_wrapper():
    """
    Test that the Bulk Retrieval tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.bulk_retrieval_tool.run.return_value = {"objects": [{"id": 1, "name": "table1"}]}

    tools_list = get_langchain_tools(mock_sdk)
    bulk_tool = next((t for t in tools_list if t.name == "AlationBulkRetrievalToolFromSDK"), None)

    assert bulk_tool is not None, "Bulk Retrieval tool should be in the tools list"
    assert bulk_tool.name == "AlationBulkRetrievalToolFromSDK"
    assert bulk_tool.description == "Provides bulk retrieval from Alation. Sourced from SDK's bulk_retrieval."

    # Test the tool function
    test_signature = {"table": {"fields_required": ["name", "url"], "limit": 10}}
    result = bulk_tool.func(signature=test_signature)
    mock_sdk.bulk_retrieval_tool.run.assert_called_once_with(signature=test_signature, chat_id=None)
    assert result == {"objects": [{"id": 1, "name": "table1"}]}


def test_catalog_context_search_agent_tool_wrapper():
    """
    Test that the Catalog Context Search Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.catalog_context_search_agent_tool.run.return_value = {"results": ["result1", "result2"]}

    tools_list = get_langchain_tools(mock_sdk)
    catalog_tool = next((t for t in tools_list if t.name == "catalog_context_search_agent"), None)

    assert catalog_tool is not None, "Catalog Context Search Agent tool should be in the tools list"
    assert catalog_tool.name == "catalog_context_search_agent"
    assert catalog_tool.description == "Catalog Context Search Agent"

    # Test the tool function
    result = catalog_tool.func(message="search for tables")
    mock_sdk.catalog_context_search_agent_tool.run.assert_called_once_with(
        message="search for tables", chat_id=None
    )
    assert result == {"results": ["result1", "result2"]}


def test_check_job_status_tool_wrapper():
    """
    Test that the Check Job Status tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.check_job_status_tool.run.return_value = {"status": "completed"}

    tools_list = get_langchain_tools(mock_sdk)
    job_tool = next((t for t in tools_list if t.name == "CheckJobStatusToolFromSDK"), None)

    assert job_tool is not None, "Check Job Status tool should be in the tools list"
    assert job_tool.name == "CheckJobStatusToolFromSDK"
    assert job_tool.description == "Checks job status via SDK's check_job_status_tool."

    # Test the tool function
    result = job_tool.func(job_id=123)
    mock_sdk.check_job_status_tool.run.assert_called_once_with(job_id=123)
    assert result == {"status": "completed"}


def test_check_data_quality_tool_wrapper():
    """
    Test that the Check Data Quality tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.check_data_quality_tool.run.return_value = {"quality_score": 85}

    tools_list = get_langchain_tools(mock_sdk)
    dq_tool = next((t for t in tools_list if t.name == "CheckDataQualityToolFromSDK"), None)

    assert dq_tool is not None, "Check Data Quality tool should be in the tools list"
    assert dq_tool.name == "CheckDataQualityToolFromSDK"
    assert dq_tool.description == "Checks data quality via SDK's check_data_quality_tool."

    # Test the tool function
    result = dq_tool.func(table_ids=[1, 2, 3], ds_id=10)
    mock_sdk.check_data_quality_tool.run.assert_called_once_with(
        table_ids=[1, 2, 3],
        sql_query=None,
        db_uri=None,
        ds_id=10,
        bypassed_dq_sources=None,
        default_schema_name="public",
        output_format="JSON",
        dq_score_threshold=None,
    )
    assert result == {"quality_score": 85}


def test_generate_data_product_tool_wrapper():
    """
    Test that the Generate Data Product tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.generate_data_product_tool.run.return_value = {"schema": "generated schema"}

    tools_list = get_langchain_tools(mock_sdk)
    gen_tool = next((t for t in tools_list if t.name == "GenerateDataProductToolFromSDK"), None)

    assert gen_tool is not None, "Generate Data Product tool should be in the tools list"
    assert gen_tool.name == "GenerateDataProductToolFromSDK"
    assert gen_tool.description == "Generates data product schemas from SDK's generate_data_product_tool."

    # Test the tool function
    result = gen_tool.func()
    mock_sdk.generate_data_product_tool.run.assert_called_once_with()
    assert result == {"schema": "generated schema"}


def test_custom_field_definitions_tool_wrapper():
    """
    Test that the Custom Field Definitions tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.get_custom_fields_definitions_tool.run.return_value = {"fields": [{"name": "field1"}]}

    tools_list = get_langchain_tools(mock_sdk)
    fields_tool = next((t for t in tools_list if t.name == "get_custom_fields_definitions"), None)

    assert fields_tool is not None, "Custom Field Definitions tool should be in the tools list"
    assert fields_tool.name == "get_custom_fields_definitions"
    assert fields_tool.description == "Gets custom field definitions"

    # Test the tool function
    result = fields_tool.func()
    mock_sdk.get_custom_fields_definitions_tool.run.assert_called_once_with(chat_id=None)
    assert result == {"fields": [{"name": "field1"}]}


def test_data_dictionary_instructions_tool_wrapper():
    """
    Test that the Data Dictionary Instructions tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.get_data_dictionary_instructions_tool.run.return_value = {"instructions": "test instructions"}

    tools_list = get_langchain_tools(mock_sdk)
    dd_tool = next((t for t in tools_list if t.name == "get_data_dictionary_instructions"), None)

    assert dd_tool is not None, "Data Dictionary Instructions tool should be in the tools list"
    assert dd_tool.name == "get_data_dictionary_instructions"
    assert dd_tool.description == "Gets data dictionary instructions"

    # Test the tool function
    result = dd_tool.func()
    mock_sdk.get_data_dictionary_instructions_tool.run.assert_called_once_with()
    assert result == {"instructions": "test instructions"}


def test_data_products_tool_wrapper():
    """
    Test that the Data Products tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.data_product_tool.run.return_value = {"products": [{"id": "dp1", "name": "Product1"}]}

    tools_list = get_langchain_tools(mock_sdk)
    dp_tool = next((t for t in tools_list if t.name == "AlationDataProductsToolFromSDK"), None)

    assert dp_tool is not None, "Data Products tool should be in the tools list"
    assert dp_tool.name == "AlationDataProductsToolFromSDK"
    assert dp_tool.description == "Provides data products from Alation. Sourced from SDK's data_product_tool."

    # Test the tool function
    result = dp_tool.func(product_id="dp1")
    mock_sdk.data_product_tool.run.assert_called_once_with(product_id="dp1", query=None)
    assert result == {"products": [{"id": "dp1", "name": "Product1"}]}


def test_data_sources_tool_wrapper():
    """
    Test that the Data Sources tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.get_data_sources_tool.run.return_value = {"sources": [{"id": 1, "name": "DB1"}]}

    tools_list = get_langchain_tools(mock_sdk)
    ds_tool = next((t for t in tools_list if t.name == "get_data_sources"), None)

    assert ds_tool is not None, "Data Sources tool should be in the tools list"
    assert ds_tool.name == "get_data_sources"
    assert ds_tool.description == "Get Data Sources"

    # Test the tool function
    result = ds_tool.func(limit=50)
    mock_sdk.get_data_sources_tool.run.assert_called_once_with(limit=50, chat_id=None)
    assert result == {"sources": [{"id": 1, "name": "DB1"}]}


def test_lineage_tool_wrapper():
    """
    Test that the Lineage tool wrapper works correctly.
    """
    from alation_ai_agent_sdk import AlationTools

    mock_sdk = get_sdk_mock()
    # Enable the lineage tool (it's a beta tool)
    mock_sdk.enabled_beta_tools.add(AlationTools.LINEAGE)
    mock_sdk.lineage_tool.run.return_value = {"lineage": "test lineage data"}

    tools_list = get_langchain_tools(mock_sdk)
    lineage_tool = next((t for t in tools_list if t.name == "GetLineageToolFromSDK"), None)

    assert lineage_tool is not None, "Lineage tool should be in the tools list"
    assert lineage_tool.name == "GetLineageToolFromSDK"
    assert lineage_tool.description == "Provides lineage from SDK"

    # Test the tool function
    from alation_ai_agent_sdk.lineage import LineageRootNode
    root_node = LineageRootNode(otype="table", oid=123)
    result = lineage_tool.func(root_node=root_node, direction="downstream")

    # Check that run was called with the expected arguments
    call_args = mock_sdk.lineage_tool.run.call_args
    assert call_args.kwargs["root_node"] == root_node
    assert call_args.kwargs["direction"] == "downstream"
    assert result == {"lineage": "test lineage data"}


def test_query_flow_agent_tool_wrapper():
    """
    Test that the Query Flow Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.query_flow_agent_tool.run.return_value = {"query_response": "flow result"}

    tools_list = get_langchain_tools(mock_sdk)
    qf_tool = next((t for t in tools_list if t.name == "query_flow_agent"), None)

    assert qf_tool is not None, "Query Flow Agent tool should be in the tools list"
    assert qf_tool.name == "query_flow_agent"
    assert qf_tool.description == "Query Flow Agent"

    # Test the tool function
    result = qf_tool.func(message="test query flow", marketplace_id="test")
    mock_sdk.query_flow_agent_tool.run.assert_called_once_with(
        message="test query flow", marketplace_id="test", chat_id=None
    )
    assert result == {"query_response": "flow result"}


def test_signature_creation_tool_wrapper():
    """
    Test that the Signature Creation tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.signature_creation_tool.run.return_value = {"signature": "test signature"}

    tools_list = get_langchain_tools(mock_sdk)
    sig_tool = next((t for t in tools_list if t.name == "get_signature_creation_instructions"), None)

    assert sig_tool is not None, "Signature Creation tool should be in the tools list"
    assert sig_tool.name == "get_signature_creation_instructions"
    assert sig_tool.description == "Gets signature creation instructions"

    # Test the tool function
    result = sig_tool.func()
    mock_sdk.signature_creation_tool.run.assert_called_once_with(chat_id=None)
    assert result == {"signature": "test signature"}


def test_sql_query_agent_tool_wrapper():
    """
    Test that the SQL Query Agent tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.sql_query_agent_tool.run.return_value = {"sql_result": "query executed"}

    tools_list = get_langchain_tools(mock_sdk)
    sql_tool = next((t for t in tools_list if t.name == "sql_query_agent"), None)

    assert sql_tool is not None, "SQL Query Agent tool should be in the tools list"
    assert sql_tool.name == "sql_query_agent"
    assert sql_tool.description == "SQL Query Agent"

    # Test the tool function
    result = sql_tool.func(message="SELECT * FROM table", data_product_id="dp-123")
    mock_sdk.sql_query_agent_tool.run.assert_called_once_with(
        message="SELECT * FROM table", data_product_id="dp-123", chat_id=None
    )
    assert result == {"sql_result": "query executed"}


def test_update_catalog_asset_metadata_tool_wrapper():
    """
    Test that the Update Catalog Asset Metadata tool wrapper works correctly.
    """
    mock_sdk = get_sdk_mock()
    mock_sdk.update_catalog_asset_metadata_tool.run.return_value = {"updated": True}

    tools_list = get_langchain_tools(mock_sdk)
    update_tool = next((t for t in tools_list if t.name == "UpdateCatalogAssetMetadataToolFromSDK"), None)

    assert update_tool is not None, "Update Catalog Asset Metadata tool should be in the tools list"
    assert update_tool.name == "UpdateCatalogAssetMetadataToolFromSDK"
    assert update_tool.description == "Updates catalog asset metadata via SDK's update_catalog_asset_metadata_tool."

    # Test the tool function
    custom_field_values = {"field1": "value1", "field2": "value2"}
    result = update_tool.func(custom_field_values=custom_field_values)
    mock_sdk.update_catalog_asset_metadata_tool.run.assert_called_once_with(
        custom_field_values=custom_field_values
    )
    assert result == {"updated": True}
