import pytest
from unittest.mock import Mock, patch

from alation_ai_agent_sdk.event import (
    ToolEvent,
    send_event,
    track_tool_execution,
)
from alation_ai_agent_sdk.api import AlationAPI
from alation_ai_agent_sdk.errors import AlationAPIError


class TestToolEvent:
    def test_to_payload_success_case(self):
        """Test to_payload method for successful execution."""
        custom_metrics = {"query_length": 10, "result_count": 5}
        input_params = {"kwargs": {"param": "value"}}

        event = ToolEvent(
            tool_name="SearchTool",
            tool_version="2.0.0",
            input_params=input_params,
            output="search results",
            duration_ms=250.75,
            success=True,
            custom_metrics=custom_metrics,
        )

        payload = event.to_payload()

        expected_tool_metadata = {"param": "value", **custom_metrics}

        assert payload["tool_name"] == "SearchTool"
        assert payload["tool_version"] == "2.0.0"
        assert payload["tool_metadata"] == expected_tool_metadata
        assert payload["context_char_count"] == len("search results")
        assert payload["request_duration_ms"] == 250  # Should be int
        assert payload["status_code"] == 200
        assert payload["error_message"] is None
        assert "timestamp" in payload

    def test_to_payload_failure_case_with_error_dict(self):
        """Test to_payload method for failed execution."""
        error_dict = {"status_code": 500, "message": "Internal Server Error"}

        event = ToolEvent(
            tool_name="FailingTool",
            tool_version="1.0.0",
            input_params={"param": "value"},
            output={"error": "Something went wrong"},
            duration_ms=100.0,
            success=False,
            error=error_dict,
        )

        payload = event.to_payload()

        assert payload["tool_name"] == "FailingTool"
        assert payload["status_code"] == 500
        assert payload["error_message"] == "Internal Server Error"

    def test_to_payload_failure_case_with_string_error(self):
        """Test to_payload method for failed execution with string error."""
        event = ToolEvent(
            tool_name="FailingTool",
            tool_version="1.0.0",
            input_params={"param": "value"},
            output={"error": "Something went wrong"},
            duration_ms=100.0,
            success=False,
            error="String error message",
        )

        payload = event.to_payload()

        assert payload["tool_name"] == "FailingTool"
        assert payload["status_code"] == 0
        assert payload["error_message"] == "String error message"

    def test_get_tool_metadata(self):
        """Test get_tool_metadata method."""
        input_params = {"kwargs": {"param": "value"}}
        custom_metrics = {"duration_category": "fast", "result_size": "small"}

        event = ToolEvent(
            tool_name="TestTool",
            tool_version="1.0.0",
            input_params=input_params,
            output="output",
            duration_ms=100.0,
            success=True,
            custom_metrics=custom_metrics,
        )

        metadata = event.get_tool_metadata()

        expected = {"param": "value", **custom_metrics}
        assert metadata == expected


class TestSendEvent:
    """Test cases for send_event function."""

    @patch("alation_ai_agent_sdk.event.logger")
    def test_send_event_success(self, mock_logger):
        """Test send_event function with successful API call."""
        mock_api = Mock(spec=AlationAPI)
        mock_api.post_tool_event.return_value = None

        event = ToolEvent(
            tool_name="TestTool",
            tool_version="1.0.0",
            input_params={},
            output="output",
            duration_ms=100.0,
            success=True,
        )

        send_event(
            mock_api, event, timeout=10.0, max_retries=3, headers={"Custom": "Header"}
        )

        # Verify API was called with correct parameters
        mock_api.post_tool_event.assert_called_once()
        call_args = mock_api.post_tool_event.call_args

        assert call_args[0][0] == event.to_payload()  # payload argument
        assert call_args[1]["timeout"] == 10.0
        assert call_args[1]["max_retries"] == 3
        assert call_args[1]["extra_headers"] == {"Custom": "Header"}

    @patch("alation_ai_agent_sdk.event.logger")
    def test_send_event_api_error(self, mock_logger):
        """Test send_event function when API call fails."""
        mock_api = Mock(spec=AlationAPI)
        mock_api.post_tool_event.side_effect = AlationAPIError("API Error")

        event = ToolEvent(
            tool_name="TestTool",
            tool_version="1.0.0",
            input_params={},
            output="output",
            duration_ms=100.0,
            success=True,
        )

        # Should not raise exception - errors are logged but not re-raised
        send_event(mock_api, event)

        # Verify error was logged with warning level
        mock_logger.warning.assert_called_once()
        assert "Unexpected error sending event" in mock_logger.warning.call_args[0][0]

    @patch("alation_ai_agent_sdk.event.logger")
    def test_send_event_generic_exception(self, mock_logger):
        """Test send_event function when generic exception occurs."""
        mock_api = Mock(spec=AlationAPI)
        mock_api.post_tool_event.side_effect = ValueError("Some error")

        event = ToolEvent(
            tool_name="TestTool",
            tool_version="1.0.0",
            input_params={},
            output="output",
            duration_ms=100.0,
            success=True,
        )

        # Should not raise exception - errors are logged but not re-raised
        send_event(mock_api, event)

        # Verify error was logged with warning level
        mock_logger.warning.assert_called_once()
        assert "Unexpected error sending event" in mock_logger.warning.call_args[0][0]


class TestTrackToolExecution:
    """Test cases for track_tool_execution decorator."""

    def test_decorator_without_api(self):
        """Test decorator when tool has no API instance."""

        @track_tool_execution()
        def test_function(self, param1, param2="default"):
            return f"result: {param1}, {param2}"

        # Mock tool instance without api attribute
        mock_tool = Mock()
        del mock_tool.api  # Ensure no api attribute

        result = test_function(mock_tool, "test", param2="custom")

        assert result == "result: test, custom"

    def test_decorator_with_invalid_api(self):
        """Test decorator when tool has invalid API instance."""

        @track_tool_execution()
        def test_function(self, param1):
            return f"result: {param1}"

        # Mock tool instance with invalid api
        mock_tool = Mock()
        mock_tool.api = "not an AlationAPI instance"

        result = test_function(mock_tool, "test")

        assert result == "result: test"

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.send_event")
    def test_decorator_successful_execution(self, mock_send_event, mock_timer):
        """Test decorator with successful function execution."""

        @track_tool_execution(timeout=15.0, max_retries=5)
        def test_function(self, param1, param2="default"):
            return f"result: {param1}, {param2}"

        # Mock tool instance with valid API
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.api.dist_version = "test-dist-1.0"
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer
        mock_timer_instance = Mock()
        mock_timer.return_value = mock_timer_instance

        with patch("time.time", side_effect=[1000.0, 1000.5]):  # 500ms duration
            result = test_function(mock_tool, "test", param2="custom")

        # Verify function result
        assert result == "result: test, custom"

        # Verify timer was set up for background telemetry
        mock_timer.assert_called_once_with(0.0, mock_timer.call_args[0][1])
        mock_timer_instance.start.assert_called_once()
        assert mock_timer_instance.daemon is True

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.send_event")
    def test_decorator_with_custom_metrics(self, mock_send_event, mock_timer):
        """Test decorator with custom metrics function."""

        def custom_metrics_fn(input_params, output, duration_ms):
            return {
                "param_count": len(input_params.get("kwargs", {})),
                "output_length": len(str(output)),
                "is_slow": duration_ms > 1000,
            }

        @track_tool_execution(custom_metrics_fn=custom_metrics_fn)
        def test_function(self, param1, param2="default"):
            return f"result: {param1}, {param2}"

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer to capture the background function
        captured_bg_function = None

        def capture_timer_function(delay, func):
            nonlocal captured_bg_function
            captured_bg_function = func
            timer_mock = Mock()
            timer_mock.daemon = None
            return timer_mock

        mock_timer.side_effect = capture_timer_function

        with patch("time.time", side_effect=[1000.0, 1000.5]):  # 500ms duration
            test_function(mock_tool, "test", param2="custom")

        # Execute the captured background function to verify custom metrics
        assert captured_bg_function is not None
        captured_bg_function()

        # Verify send_event was called with correct parameters
        mock_send_event.assert_called_once()
        call_args = mock_send_event.call_args

        api_arg, event_arg = call_args[0]
        assert api_arg == mock_tool.api
        assert isinstance(event_arg, ToolEvent)
        assert event_arg.tool_name == "TestTool"
        assert event_arg.success is True
        assert event_arg.custom_metrics["param_count"] == 1  # one kwarg
        assert event_arg.custom_metrics["output_length"] == len("result: test, custom")
        assert event_arg.custom_metrics["is_slow"] is False

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.send_event")
    def test_decorator_with_exception(self, mock_send_event, mock_timer):
        """Test decorator when decorated function raises an exception."""

        @track_tool_execution()
        def test_function(self, param1):
            raise ValueError("Test error")

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer to capture the background function
        captured_bg_function = None

        def capture_timer_function(delay, func):
            nonlocal captured_bg_function
            captured_bg_function = func
            return Mock(daemon=None)

        mock_timer.side_effect = capture_timer_function

        with patch("time.time", side_effect=[1000.0, 1000.2]):  # 200ms duration
            with pytest.raises(ValueError, match="Test error"):
                test_function(mock_tool, "test")

        # Execute the captured background function
        captured_bg_function()

        # Verify send_event was called with error details
        mock_send_event.assert_called_once()
        call_args = mock_send_event.call_args

        event_arg = call_args[0][1]
        assert event_arg.success is False
        assert event_arg.error == "Test error"
        assert event_arg.output == {"error": "Test error"}

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.send_event")
    def test_decorator_with_unhandled_AlationAPIError(
        self, mock_send_event, mock_timer
    ):
        """Test decorator when an unhandled AlationAPIError occurs."""

        @track_tool_execution()
        def test_function(self, param1):
            raise AlationAPIError(
                "Unhandled API error",
                reason="Something went wrong",
                resolution_hint="Retry again",
            )

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer to capture the background function
        captured_bg_function = None

        def capture_timer_function(delay, func):
            nonlocal captured_bg_function
            captured_bg_function = func
            return Mock(daemon=None)

        mock_timer.side_effect = capture_timer_function

        with patch("time.time", side_effect=[1000.0, 1000.2]):  # 200ms duration
            with pytest.raises(AlationAPIError, match="Unhandled API error"):
                test_function(mock_tool, "test")

        # Execute the captured background function
        captured_bg_function()

        # Verify send_event was called with error details
        mock_send_event.assert_called_once()
        call_args = mock_send_event.call_args

        event_arg = call_args[0][1]
        assert event_arg.success is False
        assert event_arg.error == "Unhandled API error"
        assert event_arg.output == {"error": "Unhandled API error"}

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.send_event")
    def test_decorator_with_error_in_output(self, mock_send_event, mock_timer):
        """Test decorator when function returns error in output."""

        @track_tool_execution()
        def test_function(self, param1):
            return {"error": "Function returned error", "data": None}

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer to capture the background function
        captured_bg_function = None

        def capture_timer_function(delay, func):
            nonlocal captured_bg_function
            captured_bg_function = func
            return Mock(daemon=None)

        mock_timer.side_effect = capture_timer_function

        with patch("time.time", side_effect=[1000.0, 1000.1]):
            test_function(mock_tool, "test")

        # Execute the captured background function
        captured_bg_function()

        # Verify send_event was called with error from output
        mock_send_event.assert_called_once()
        event_arg = mock_send_event.call_args[0][1]

        assert event_arg.success is True  # Function didn't raise exception
        assert event_arg.error == "Function returned error"

    @patch("alation_ai_agent_sdk.event.threading.Timer")
    @patch("alation_ai_agent_sdk.event.logger")
    def test_decorator_custom_metrics_exception(self, mock_logger, mock_timer):
        """Test decorator when custom metrics function raises exception."""

        def failing_custom_metrics(input_params, output, duration_ms):
            raise RuntimeError("Custom metrics failed")

        @track_tool_execution(custom_metrics_fn=failing_custom_metrics)
        def test_function(self, param1):
            return "success"

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        # Mock timer to capture the background function
        captured_bg_function = None

        def capture_timer_function(delay, func):
            nonlocal captured_bg_function
            captured_bg_function = func
            return Mock(daemon=None)

        mock_timer.side_effect = capture_timer_function

        with patch("time.time", side_effect=[1000.0, 1000.1]):
            test_function(mock_tool, "test")

        # Execute the captured background function
        captured_bg_function()

        # Verify warning was logged about custom metrics failure
        mock_logger.warning.assert_called_once()
        assert "Error getting custom metrics" in mock_logger.warning.call_args[0][0]

    @patch("alation_ai_agent_sdk.event.logger")
    def test_decorator_timer_creation_fails(self, mock_logger):
        """Test decorator when timer creation fails."""

        @track_tool_execution()
        def test_function(self, param1):
            return "success"

        # Mock tool instance
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.__class__.__name__ = "TestTool"

        with patch(
            "alation_ai_agent_sdk.event.threading.Timer",
            side_effect=RuntimeError("Timer failed"),
        ):
            with patch("time.time", side_effect=[1000.0, 1000.1]):
                result = test_function(mock_tool, "test")

        # Function should still succeed
        assert result == "success"

        # Verify error was logged
        mock_logger.debug.assert_called_once()
        assert "Could not send telemetry event" in mock_logger.debug.call_args[0][0]

    def test_decorator_tool_version_formatting(self):
        """Test that tool version is correctly formatted with dist_version."""

        @track_tool_execution()
        def test_function(self):
            return "success"

        # Test with dist_version
        mock_tool = Mock()
        mock_tool.api = Mock(spec=AlationAPI)
        mock_tool.api.dist_version = "my-dist-2.0"
        mock_tool.__class__.__name__ = "TestTool"

        captured_event = None

        def capture_send_event(api, event, **kwargs):
            nonlocal captured_event
            captured_event = event

        with patch(
            "alation_ai_agent_sdk.event.send_event", side_effect=capture_send_event
        ):
            with patch("alation_ai_agent_sdk.event.threading.Timer") as mock_timer:
                # Set up timer to immediately call the background function
                def immediate_call(delay, func):
                    func()  # Call immediately for testing
                    return Mock(daemon=None, start=Mock())

                mock_timer.side_effect = immediate_call

                with patch("time.time", side_effect=[1000.0, 1000.1]):
                    test_function(mock_tool)

        # Verify tool version includes dist_version
        from alation_ai_agent_sdk.utils import SDK_VERSION

        expected_version = f"my-dist-2.0/sdk-{SDK_VERSION}"
        assert captured_event.tool_version == expected_version

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""

        def custom_metrics_fn(input_params, output, duration_ms):
            return {"test": "metric"}

        @track_tool_execution(custom_metrics_fn=custom_metrics_fn, timeout=10.0)
        def original_function(self, param1, param2="default"):
            """Original function docstring."""
            return f"result: {param1}, {param2}"

        # Verify function metadata is preserved
        assert original_function.__name__ == "original_function"
        assert "Original function docstring." in original_function.__doc__
