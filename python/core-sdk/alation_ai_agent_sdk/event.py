import datetime
import logging
import time
import threading
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from alation_ai_agent_sdk.utils import SDK_VERSION

from .api import AlationAPI


logger = logging.getLogger(__name__)


class ToolEvent:
    """Represents a tool event."""

    def __init__(
        self,
        tool_name: str,
        tool_version: str,
        input_params: Dict[str, Any],
        output: Any,
        duration_ms: float,
        success: bool,
        error: Optional[Union[str, dict]] = None,
        custom_metrics: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime.datetime] = None,
    ):
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.input_params = input_params
        self.output = output
        self.duration_ms = duration_ms
        self.success = success
        self.error = error
        self.custom_metrics = custom_metrics or {}
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)

    def to_payload(self) -> Dict[str, Any]:
        """
        Converts the event to a dictionary payload expected by the /tool/event endpoint

        tool_name       ->  tool_name
        input_params    ->  tool_metadata
        output          ->  context_char_count
        duration_ms     ->  request_duration_ms
        success         ->  status_code
        error           ->  status_code & error_message
        custom_metrics  ->  tool_metadata
        timestamp       ->  timestamp
        """
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "tool_metadata": self.get_tool_metadata(),
            "context_char_count": len(str(self.output)),
            "request_duration_ms": int(self.duration_ms),
            "status_code": self.get_status_code(),
            "error_message": self.get_error_message(),
            "timestamp": self.timestamp.isoformat(),
        }

    def get_tool_metadata(self) -> dict:
        """
        Gathers and returns the tool metadata by combining input parameters and custom metrics.
        """
        tool_metadata = {}
        kwargs = self.input_params.get("kwargs", {})
        tool_metadata.update(kwargs)
        tool_metadata.update(self.custom_metrics)
        return tool_metadata

    def get_status_code(self) -> int:
        """
        Tool event response is not http object, so we need the transformation to a status code
        """
        if self.success:
            return 200
        elif (
            self.error and isinstance(self.error, dict) and "status_code" in self.error
        ):
            # If the error is a dict and has a status_code, return it
            return self.error["status_code"]
        else:
            # If unknown error without status_code, return 0
            return 0

    def get_error_message(self) -> Optional[str]:
        if isinstance(self.error, str):
            return self.error
        if isinstance(self.error, dict) and "message" in self.error:
            return self.error["message"]
        return None


def send_event(
    api: AlationAPI,
    event: ToolEvent,
    timeout: float = 5.0,
    max_retries: int = 2,
    headers: Optional[Dict[str, str]] = None,
):
    """
    Sends a tool event to the Alation API.
    """
    try:
        payload = event.to_payload()
        api.post_tool_event(
            payload, timeout=timeout, max_retries=max_retries, extra_headers=headers
        )
    except Exception as e:
        # Failure to send event should be non-blocking
        logger.warning(f"Unexpected error sending event: {e}")


def track_tool_execution(
    custom_metrics_fn: Optional[Callable[[Any, Any, float], Dict[str, Any]]] = None,
    timeout: float = 5.0,
    max_retries: int = 2,
    headers: Optional[Dict[str, str]] = None,
):
    """
    Decorator to send tool execution events. Used for synchronous tool execution.

    Args:
        custom_metrics_fn: Optional function that takes (input_params, output, duration_ms)
                          and returns custom metrics dict
        timeout: Request timeout in seconds for telemetry requests
        max_retries: Number of retry attempts for failed telemetry requests
        headers: Additional headers to include in telemetry requests

    Example:
        # Using a function
        def get_query_metrics(input_params, output, duration_ms):
            return {
                "query_length": len(input_params.get("kwargs", {}).get("question", "")),
                "result_count": len(output) if isinstance(output, list) else 1,
                "is_slow_query": duration_ms > 5000
            }

        @track_tool_execution(custom_metrics_fn=get_query_metrics)
        def run(self, question: str):
            return self.api.search(question)

        # Using a lambda (simpler)
        @track_tool_execution(
            custom_metrics_fn=lambda inp, out, dur: {"duration_category": "slow" if dur > 1000 else "fast"}
        )
        def run(self, question: str):
            return self.api.search(question)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get the API instance from the tool
            api = getattr(self, "api", None)
            if not api or not isinstance(api, AlationAPI):
                # No API available, just run the function without telemetry
                return func(self, *args, **kwargs)

            # Capture input parameters
            input_params = {}
            if args:
                input_params["args"] = args
            if kwargs:
                input_params["kwargs"] = kwargs

            start_time = time.time()
            success = True
            error = None
            output = None

            try:
                output = func(self, *args, **kwargs)
                return output
            except Exception as e:
                success = False
                output = {"error": str(e)}
                raise
            finally:
                # Capture the duration
                duration_ms = (time.time() - start_time) * 1000

                # Capture error from the response output
                if output and isinstance(output, dict) and "error" in output:
                    error = output["error"]

                # Capture tool version as dist_version/sdk_version
                tool_version = f"sdk-{SDK_VERSION}"
                api = getattr(self, "api", None)
                if (
                    api
                    and isinstance(api, AlationAPI)
                    and hasattr(api, "dist_version")
                    and api.dist_version
                ):
                    tool_version = f"{api.dist_version}/{tool_version}"

                # Get custom metrics if function provided
                custom_metrics = {}
                if custom_metrics_fn:
                    try:
                        custom_metrics = custom_metrics_fn(
                            input_params, output, duration_ms
                        )
                    except Exception as e:
                        logger.warning(f"Error getting custom metrics: {e}")

                # Create an event
                event = ToolEvent(
                    tool_name=self.__class__.__name__,
                    tool_version=tool_version,
                    input_params=input_params,
                    output=output,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    custom_metrics=custom_metrics,
                )

                try:

                    def send_in_background():
                        send_event(
                            api,
                            event,
                            timeout=timeout,
                            max_retries=max_retries,
                            headers=headers,
                        )

                    # This creates a thread to send the event in the background.
                    # It's a simple solution that works for low frequency events
                    # but needs improvement for high frequency events
                    # I've also considered using async.create_task(), but we don't have
                    # async yet, and even then it runs in the same thread there may not be
                    # much perf gain.
                    timer = threading.Timer(0.0, send_in_background)
                    timer.daemon = True
                    timer.start()
                except Exception as e:
                    logger.debug(f"Could not send telemetry event: {e}")

        return wrapper

    return decorator
