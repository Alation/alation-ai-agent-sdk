import requests
import pytest
import os
from unittest.mock import patch, MagicMock
from alation_ai_agent_mcp import server
from alation_ai_agent_mcp.utils import MCP_SERVER_VERSION
from alation_ai_agent_sdk import (
    AlationTools,
    UserAccountAuthParams,
    ServiceAccountAuthParams,
)


@pytest.fixture(autouse=True)
def global_network_mocks(monkeypatch):
    # Mock requests.post for token generation
    def mock_post(url, *args, **kwargs):
        if "createAPIAccessToken" in url or "oauth/v2/token" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {
                "api_access_token": "mock-access-token",
                "access_token": "mock-jwt-access-token",
                "status": "success",
            }
            return response
        return MagicMock(status_code=200, json=MagicMock(return_value={}))

    monkeypatch.setattr(requests, "post", mock_post)

    # Mock requests.get for license and version
    def mock_get(url, *args, **kwargs):
        if "/api/v1/license" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"is_cloud": True}
            return response
        if "/full_version" in url:
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"ALATION_RELEASE_NAME": "2025.1.2"}
            return response
        return MagicMock(status_code=200, json=MagicMock(return_value={}))

    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture(autouse=True)
def manage_environment_variables(monkeypatch):
    """Fixture to manage environment variables for tests."""
    original_vars = {
        "ALATION_BASE_URL": os.environ.get("ALATION_BASE_URL"),
        "ALATION_AUTH_METHOD": os.environ.get("ALATION_AUTH_METHOD"),
        "ALATION_USER_ID": os.environ.get("ALATION_USER_ID"),
        "ALATION_REFRESH_TOKEN": os.environ.get("ALATION_REFRESH_TOKEN"),
        "ALATION_CLIENT_ID": os.environ.get("ALATION_CLIENT_ID"),
        "ALATION_CLIENT_SECRET": os.environ.get("ALATION_CLIENT_SECRET"),
    }
    monkeypatch.setenv("ALATION_BASE_URL", "https://mock-alation.com")
    monkeypatch.setenv("ALATION_AUTH_METHOD", "user_account")
    monkeypatch.setenv("ALATION_USER_ID", "12345")
    monkeypatch.setenv("ALATION_REFRESH_TOKEN", "mock-token")
    yield
    for key, value in original_vars.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.fixture()
def manage_disabled_tools_and_enabled_beta_tools_environment(monkeypatch):
    """
    Fixture to set environment variables for disabled tools and enabled beta tools.
    This is used to test the server creation with specific tool configurations.
    """
    monkeypatch.setenv(
        "ALATION_DISABLED_TOOLS", ",".join([AlationTools.AGGREGATED_CONTEXT])
    )
    monkeypatch.setenv("ALATION_ENABLED_BETA_TOOLS", ",".join([AlationTools.LINEAGE]))
    yield
    monkeypatch.delenv("ALATION_DISABLED_TOOLS", raising=False)
    monkeypatch.delenv("ALATION_ENABLED_BETA_TOOLS", raising=False)


@pytest.fixture
def mock_alation_sdk():
    """Fixture to mock the AlationAIAgentSDK within the installed package."""
    mock_sdk_instance = MagicMock()
    mock_sdk_instance.context_tool = MagicMock()
    mock_sdk_instance.context_tool.name = "mock_alation_context_tool"
    mock_sdk_instance.context_tool.description = (
        "Mock description for Alation context tool."
    )
    mock_sdk_instance.get_context.return_value = {"data": "mock context data"}

    patch_target = "alation_ai_agent_mcp.server.AlationAIAgentSDK"
    with patch(patch_target, return_value=mock_sdk_instance) as mock_sdk_class:
        yield mock_sdk_class, mock_sdk_instance


@pytest.fixture
def mock_fastmcp():
    """Fixture to mock the FastMCP server within the installed package."""
    mock_mcp_instance = MagicMock()
    mock_mcp_instance.tools = {}

    def mock_tool_decorator(name, description):
        def decorator(func):
            print("registering MCP tool name:", name)
            mock_mcp_instance.tools[name] = MagicMock(__wrapped__=func)
            mock_mcp_instance.tools[description] = MagicMock(__wrapped__=func)
            return func

        return decorator

    mock_mcp_instance.tool.side_effect = mock_tool_decorator
    patch_target = "alation_ai_agent_mcp.server.FastMCP"
    with patch(patch_target, return_value=mock_mcp_instance) as mock_mcp_class:
        yield mock_mcp_class, mock_mcp_instance


# -- tests


def test_create_server_missing_env_var(manage_environment_variables, monkeypatch):
    """
    Test that create_server raises ValueError if an environment variable is missing.
    """
    monkeypatch.delenv("ALATION_BASE_URL")
    with pytest.raises(ValueError, match="Missing Alation base URL"):
        server.create_server("stdio")


def test_create_server_invalid_user_id_env_var(
    manage_environment_variables, monkeypatch
):
    """
    Test that create_server raises ValueError if ALATION_USER_ID is not an integer.
    """
    monkeypatch.setenv("ALATION_USER_ID", "not-an-int")
    with pytest.raises(ValueError):
        server.create_server("stdio")


def test_create_server_success(
    manage_environment_variables, mock_alation_sdk, mock_fastmcp
):
    """
    Test successful creation of the server and SDK initialization using installed package code.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    mcp_result = server.create_server("stdio")

    mock_mcp_class.assert_called_once_with(name="Alation MCP Server")
    mock_sdk_class.assert_called_once_with(
        "https://mock-alation.com",
        "user_account",
        UserAccountAuthParams(12345, "mock-token"),
        dist_version=f"mcp-{MCP_SERVER_VERSION}",
    )
    assert mcp_result is mock_mcp_instance


def test_create_server_disabled_tool_and_enabled_beta_tool(
    manage_environment_variables, mock_fastmcp
):
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    mock_mcp_instance.reset_mock()

    mcp_result = server.create_server(
        "stdio",
        disabled_tools_str=AlationTools.AGGREGATED_CONTEXT,
        enabled_beta_tools_str=AlationTools.LINEAGE,
    )

    mock_mcp_class.assert_called_once_with(name="Alation MCP Server")
    assert mcp_result is mock_mcp_instance
    # of 10 possible tools 9 tools are on by default with one 1 beta available

    assert mock_mcp_instance.tool.call_count == 9

    # NOTE: each distribution may refer to the tools differently. These should be standardized so we can
    # reuse a set of constants across all projects.
    assert "alation_context" not in mock_mcp_instance.tools

    assert "bulk_retrieval" in mock_mcp_instance.tools
    assert "get_data_products" in mock_mcp_instance.tools
    assert "update_catalog_asset_metadata" in mock_mcp_instance.tools
    assert "check_job_status" in mock_mcp_instance.tools
    assert "get_lineage" in mock_mcp_instance.tools
    assert "generate_data_product" in mock_mcp_instance.tools


def test_create_server_disabled_tool_and_enabled_beta_tool_via_environment(
    manage_environment_variables,
    manage_disabled_tools_and_enabled_beta_tools_environment,
    mock_fastmcp,
):
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    mock_mcp_instance.reset_mock()

    # The manage fixture is the source of the disabled tools as well as the enabled beta tools
    mcp_result = server.create_server("stdio")

    mock_mcp_class.assert_called_once_with(name="Alation MCP Server")
    assert mcp_result is mock_mcp_instance

    assert mock_mcp_instance.tool.call_count == 9

    # NOTE: each distribution may refer to the tools differently. These should be standardized so we can
    # reuse a set of constants across all projects.
    assert "alation_context" not in mock_mcp_instance.tools

    assert "bulk_retrieval" in mock_mcp_instance.tools
    assert "get_data_products" in mock_mcp_instance.tools
    assert "update_catalog_asset_metadata" in mock_mcp_instance.tools
    assert "check_job_status" in mock_mcp_instance.tools
    assert "get_lineage" in mock_mcp_instance.tools
    assert "generate_data_product" in mock_mcp_instance.tools


def test_tool_registration(
    manage_environment_variables, mock_alation_sdk, mock_fastmcp
):
    """
    Test that the alation_context tool is registered correctly on the mocked MCP.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    server.create_server("stdio")

    # Check that tools are registered
    # The tool name is now determined by get_tool_metadata() from the actual tool class
    tool_name = "alation_context"  # AlationContextTool._get_name()
    assert tool_name in mock_mcp_instance.tools
    assert isinstance(mock_mcp_instance.tools[tool_name], MagicMock)
    assert hasattr(mock_mcp_instance.tools[tool_name], "__wrapped__")


def test_alation_context_tool_logic(
    manage_environment_variables, mock_alation_sdk, mock_fastmcp
):
    """
    Test the logic within the registered alation_context tool function itself.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    server.create_server("stdio")

    # The tool name is now determined by get_tool_metadata() from the actual tool class
    tool_name = "alation_context"  # AlationContextTool._get_name()
    registered_tool_mock = mock_mcp_instance.tools.get(tool_name)
    assert registered_tool_mock is not None, (
        f"Tool '{tool_name}' was not registered on the mock MCP."
    )
    tool_func = registered_tool_mock.__wrapped__
    assert callable(tool_func), "Registered tool is not callable"

    # Test case 1: Call with only question
    question_input = "What is the definition of 'Data Catalog'?"
    expected_sdk_result = {"data": "mock context data for question"}
    mock_sdk_instance.get_context.return_value = expected_sdk_result

    result = tool_func(question=question_input)

    mock_sdk_instance.get_context.assert_called_once_with(question_input, None)
    assert result == expected_sdk_result

    mock_sdk_instance.get_context.reset_mock()

    # Test case 2: Call with question and signature
    signature_input = {"object_id": 123, "object_type": "table"}
    expected_sdk_result_sig = {"data": "mock context data with signature"}
    mock_sdk_instance.get_context.return_value = expected_sdk_result_sig

    result_sig = tool_func(question=question_input, signature=signature_input)

    mock_sdk_instance.get_context.assert_called_once_with(
        question_input, signature_input
    )
    assert result_sig == expected_sdk_result_sig


@patch("alation_ai_agent_mcp.server.create_server")
def test_run_server_calls_create_and_run(mock_create_server, mock_fastmcp):
    """
    Test that run_server calls create_server and mcp.run().
    """
    mock_mcp_class, mock_mcp_instance = mock_fastmcp
    mock_create_server.return_value = mock_mcp_instance

    server.run_server()

    mock_create_server.assert_called_once()
    mock_mcp_instance.run.assert_called_once()


def test_create_server_service_account(
    manage_environment_variables, monkeypatch, mock_alation_sdk, mock_fastmcp
):
    """
    Test successful creation of the server with service_account authentication.
    """
    # Set environment variables for service_account auth method
    monkeypatch.setenv("ALATION_AUTH_METHOD", "service_account")
    monkeypatch.setenv("ALATION_CLIENT_ID", "mock-client-id")
    monkeypatch.setenv("ALATION_CLIENT_SECRET", "mock-client-secret")

    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    mcp_result = server.create_server("stdio")

    mock_mcp_class.assert_called_once_with(name="Alation MCP Server")
    mock_sdk_class.assert_called_once_with(
        "https://mock-alation.com",
        "service_account",
        ServiceAccountAuthParams("mock-client-id", "mock-client-secret"),
        dist_version=f"mcp-{MCP_SERVER_VERSION}",
    )
    assert mcp_result is mock_mcp_instance


@patch("alation_ai_agent_mcp.server.create_server")
def test_run_server_cli_no_arguments(mock_create_server):
    with patch("alation_ai_agent_mcp.server.parse_arguments") as mock_parse_args:
        mock_parse_args.return_value = ("stdio", None, None, None, None, None, None)

        server.run_server()

        mock_create_server.assert_called_once()
        mock_create_server.assert_called_with(
            "stdio", None, None, None, None, None, None
        )


@patch("alation_ai_agent_mcp.server.create_server")
def test_run_server_cli_with_arguments(mock_create_server):
    with patch("alation_ai_agent_mcp.server.parse_arguments") as mock_parse_args:
        mock_parse_args.return_value = (
            "stdio",
            None,
            "tool1,tool2",
            "tool3",
            None,
            None,
            None,
        )

        server.run_server()

        mock_create_server.assert_called_once()
        mock_create_server.assert_called_with(
            "stdio", None, "tool1,tool2", "tool3", None, None, None
        )
