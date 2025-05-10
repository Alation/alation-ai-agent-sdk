import os
import pytest
from unittest.mock import patch, MagicMock
from alation_ai_agent_mcp import server


@pytest.fixture(autouse=True)
def manage_environment_variables(monkeypatch):
    """Fixture to manage environment variables for tests."""
    original_vars = {
        "ALATION_BASE_URL": os.environ.get("ALATION_BASE_URL"),
        "ALATION_USER_ID": os.environ.get("ALATION_USER_ID"),
        "ALATION_REFRESH_TOKEN": os.environ.get("ALATION_REFRESH_TOKEN"),
    }
    monkeypatch.setenv("ALATION_BASE_URL", "https://fake-alation.com")
    monkeypatch.setenv("ALATION_USER_ID", "12345")
    monkeypatch.setenv("ALATION_REFRESH_TOKEN", "fake-token")
    yield
    for key, value in original_vars.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.fixture
def mock_alation_sdk():
    """Fixture to mock the AlationAIAgentSDK within the installed package."""
    mock_sdk_instance = MagicMock()
    mock_sdk_instance.context_tool = MagicMock()
    mock_sdk_instance.context_tool.name = "mock_alation_context_tool"
    mock_sdk_instance.context_tool.description = "Mock description for Alation context tool."
    mock_sdk_instance.get_context.return_value = {"data": "mock context data"}

    patch_target = "alation_ai_agent_mcp.server.AlationAIAgentSDK"
    with patch(patch_target, return_value=mock_sdk_instance) as mock_sdk_class:
        yield mock_sdk_class, mock_sdk_instance


@pytest.fixture
def mock_fastmcp():
    """Fixture to mock the FastMCP server within the installed package."""
    mock_mcp_instance = MagicMock()
    mock_mcp_instance.tools = {}

    def mock_tool_decorator(name):
        def decorator(func):
            mock_mcp_instance.tools[name] = MagicMock(__wrapped__=func)
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
    with pytest.raises(ValueError, match="Missing required environment variables"):
        server.create_server()


def test_create_server_invalid_user_id_env_var(manage_environment_variables, monkeypatch):
    """
    Test that create_server raises ValueError if ALATION_USER_ID is not an integer.
    """
    monkeypatch.setenv("ALATION_USER_ID", "not-an-int")
    with pytest.raises(ValueError):
        server.create_server()


def test_create_server_success(manage_environment_variables, mock_alation_sdk, mock_fastmcp):
    """
    Test successful creation of the server and SDK initialization using installed package code.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    mcp_result = server.create_server()

    mock_mcp_class.assert_called_once_with(name="Alation MCP Server", version="0.1.0")
    mock_sdk_class.assert_called_once_with("https://fake-alation.com", 12345, "fake-token")
    assert mcp_result is mock_mcp_instance


def test_tool_registration(manage_environment_variables, mock_alation_sdk, mock_fastmcp):
    """
    Test that the alation_context tool is registered correctly on the mocked MCP.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    server.create_server()

    expected_tool_name = mock_sdk_instance.context_tool.name
    mock_mcp_instance.tool.assert_called_once_with(name=expected_tool_name)
    assert expected_tool_name in mock_mcp_instance.tools
    assert isinstance(mock_mcp_instance.tools[expected_tool_name], MagicMock)
    assert hasattr(mock_mcp_instance.tools[expected_tool_name], "__wrapped__")


def test_alation_context_tool_logic(manage_environment_variables, mock_alation_sdk, mock_fastmcp):
    """
    Test the logic within the registered alation_context tool function itself.
    """
    mock_sdk_class, mock_sdk_instance = mock_alation_sdk
    mock_mcp_class, mock_mcp_instance = mock_fastmcp

    server.create_server()

    tool_name = mock_sdk_instance.context_tool.name
    registered_tool_mock = mock_mcp_instance.tools.get(tool_name)
    assert (
        registered_tool_mock is not None
    ), f"Tool '{tool_name}' was not registered on the mock MCP."
    tool_func = registered_tool_mock.__wrapped__
    assert callable(tool_func), "Registered tool is not callable"

    # Test case 1: Call with only question
    question_input = "What is the definition of 'Data Catalog'?"
    expected_sdk_result = {"data": "mock context data for question"}
    mock_sdk_instance.get_context.return_value = expected_sdk_result

    result = tool_func(question=question_input)

    mock_sdk_instance.get_context.assert_called_once_with(question_input, None)
    assert result == str(expected_sdk_result)

    mock_sdk_instance.get_context.reset_mock()

    # Test case 2: Call with question and signature
    signature_input = {"object_id": 123, "object_type": "table"}
    expected_sdk_result_sig = {"data": "mock context data with signature"}
    mock_sdk_instance.get_context.return_value = expected_sdk_result_sig

    result_sig = tool_func(question=question_input, signature=signature_input)

    mock_sdk_instance.get_context.assert_called_once_with(question_input, signature_input)
    assert result_sig == str(expected_sdk_result_sig)


@patch("alation_ai_agent_mcp.server.create_server")
def test_run_server_calls_create_and_run(mock_create_server, mock_fastmcp):
    """
    Test that run_server calls create_server and mcp.run().
    """
    mock_mcp_class, mock_mcp_instance = mock_fastmcp
    mock_create_server.return_value = mock_mcp_instance
    server.mcp = None  # Reset global before test

    server.run_server()

    mock_create_server.assert_called_once()
    mock_mcp_instance.run.assert_called_once()
    assert server.mcp is mock_mcp_instance
