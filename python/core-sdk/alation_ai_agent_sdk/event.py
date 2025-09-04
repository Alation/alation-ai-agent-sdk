import datetime
import time
import logging
import asyncio
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
import httpx

from .api import AlationAPI

# Set the global logging level to INFO
logging.basicConfig(level=logging.INFO)

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
        self.timestamp = timestamp or datetime.datetime.now(datetime.UTC)

    def to_payload(self) -> Dict[str, Any]:
        """Convert the event to a dictionary payload expected by the /tool/event endpoint"""
        """
        tool_name       ->  tool_name
        input_params    ->  tool_metadata
        output          ->  context_char_count
        duration_ms     ->  request_duration_ms
        success         ->  status_code
        error           ->  status_code & error_message
        custom_metrics  ->  tool_metadata
        timestamp       ->  timestamp
        """
        tool_metadata = {}
        tool_metadata.update(self.input_params)
        tool_metadata.update(self.custom_metrics)

        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "tool_metadata": tool_metadata,
            "context_char_count": len(self.output),
            "request_duration_ms": int(self.duration_ms),
            "status_code": self.get_status_code(self.success, self.error),
            "error_message": self.get_error_message(self.error),
            "timestamp": self.timestamp.isoformat(),
        }

    def get_status_code(self, success: bool, error: Optional[Union[str, dict]]) -> int:
        if success:
            return 200
        elif error and isinstance(error, dict) and "status_code" in error:
            # If the error is a dict and has a status_code, return it
            return error["status_code"]
        else:
            return 0

    def get_error_message(self, error: Optional[Union[str, dict]]) -> Optional[str]:
        if isinstance(error, str):
            return error
        if isinstance(error, dict) and "message" in error:
            return error["message"]
        return None


class EventTracker:
    """Handles tool event tracking and sending."""

    def __init__(
        self,
        api: AlationAPI,
        timeout: float = 5.0,
        max_retries: int = 2,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.api = api
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {}

    async def send_event_async(self, event: ToolEvent):
        """Send the event to the event tracking endpoint asynchronously."""
        try:
            payload = event.to_payload()
            logger.debug(f"Payload: {payload}")

            for attempt in range(self.max_retries + 1):
                try:
                    await self.api.post_tool_event_async(
                        payload, timeout=self.timeout, extra_headers=self.headers
                    )
                    logger.debug(f"Event sent successfully: {event.tool_name}")
                    return
                except httpx.RequestError as e:
                    if attempt == self.max_retries:
                        logger.warning(
                            f"Failed to send event after {self.max_retries + 1} attempts: {e}"
                        )
                    else:
                        logger.debug(
                            f"Event send attempt {attempt + 1} failed, retrying: {e}"
                        )
                        await asyncio.sleep(0.1 * (2**attempt))  # Exponential backoff
        except asyncio.CancelledError:
            # Handle cancellation gracefully - this is expected for fire-and-forget tasks
            logger.debug(f"Telemetry task cancelled for {event.tool_name}")
        except Exception as e:
            logger.error(f"Unexpected error sending event: {e}")

    def send_event(self, event: ToolEvent):
        """Send the event synchronously using httpx.Client (for background threads)."""
        try:
            payload = event.to_payload()
            logger.debug(f"Payload: {payload}")

            for attempt in range(self.max_retries + 1):
                try:
                    self.api.post_tool_event(
                        payload, timeout=self.timeout, extra_headers=self.headers
                    )
                    logger.debug(f"Event sent successfully: {event.tool_name}")
                    return
                except httpx.RequestError as e:
                    if attempt == self.max_retries:
                        logger.warning(
                            f"Failed to send event after {self.max_retries + 1} attempts: {e}"
                        )
                    else:
                        logger.debug(
                            f"Event send attempt {attempt + 1} failed, retrying: {e}"
                        )
                        time.sleep(0.1 * (2**attempt))  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error sending event: {e}")


# Global event tracker instance
_event_tracker: Optional[EventTracker] = None


def create_event_tracker(
    api: AlationAPI,
    timeout: float = 5.0,
    max_retries: int = 2,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[EventTracker]:
    """
    Get existing event tracker or create one if base_url is provided.

    Args:
        base_url: Base URL for the event tracking endpoint (will append '/tool/event')
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts for failed requests
        headers: Additional headers to include in requests

    Returns:
        EventTracker instance if base_url provided or already configured, None otherwise
    """
    global _event_tracker

    # Return existing tracker if available
    if _event_tracker is not None:
        return _event_tracker

    _event_tracker = EventTracker(
        api=api,
        timeout=timeout,
        max_retries=max_retries,
        headers=headers,
    )
    return _event_tracker


def get_event_tracker() -> Optional[EventTracker]:
    """Get the global event tracker."""
    return _event_tracker


def track_tool_execution(
    custom_metrics_fn: Optional[Callable[[Any, Any, float], Dict[str, Any]]] = None,
):
    """
    Decorator to send tool execution events. Used for synchronous tool execution.

    Args:
        custom_metrics_fn: Optional function that takes (input_params, output, duration_ms)
                          and returns custom metrics dict

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
            tracker = get_event_tracker()

            if not tracker:
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
                duration_ms = (time.time() - start_time) * 1000
                if output and isinstance(output, dict) and "error" in output:
                    error = output["error"]

                tool_version = getattr(self.__class__, "sdk_version", "Unknown")

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

                # Handle event sending - use simple fire-and-forget approach
                try:
                    import threading

                    def send_in_background():
                        # Use the synchronous method to avoid event loop issues
                        tracker.send_event(event)

                    # Use Timer with immediate execution (0 delay)
                    timer = threading.Timer(0.0, send_in_background)
                    timer.daemon = True
                    timer.start()
                except Exception as e:
                    logger.debug(f"Could not send telemetry event: {e}")

        return wrapper

    return decorator


def track_async_tool_execution(
    custom_metrics_fn: Optional[Callable[[Any, Any, float], Dict[str, Any]]] = None,
):
    """
    Decorator to send tool execution events. Used for asynchronous tool execution.

    Args:
        custom_metrics_fn: Optional function that takes (input_params, output, duration_ms)
                          and returns custom metrics dict

    Example:
        # Using a function
        def get_lineage_metrics(input_params, output, duration_ms):
            return {
                "direction": input_params.get("kwargs", {}).get("direction", "unknown"),
                "node_count": len(output.get("nodes", [])) if isinstance(output, dict) else 0,
                "is_large_graph": duration_ms > 10000
            }

        @track_async_tool_execution(custom_metrics_fn=get_lineage_metrics)
        async def run(self, root_node, direction):
            return await self.api.get_lineage(root_node, direction)

        # Using a lambda (simpler)
        @track_async_tool_execution(
            custom_metrics_fn=lambda inp, out, dur: {"performance": "good" if dur < 5000 else "needs_optimization"}
        )
        async def run(self, root_node, direction):
            return await self.api.get_lineage(root_node, direction)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            tracker = get_event_tracker()

            if not tracker:
                return await func(self, *args, **kwargs)

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
                output = await func(self, *args, **kwargs)
                return output
            except Exception as e:
                success = False
                output = {"error": str(e)}
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                if output and isinstance(output, dict) and "error" in output:
                    error = output["error"]

                tool_version = getattr(self.__class__, "sdk_version", "Unknown")

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
                # await asyncio.create_task(tracker.send_event_async(event))
                try:
                    import threading

                    async def send_in_background():
                        # Use the synchronous method to avoid event loop issues
                        await tracker.send_event_async(event)

                    # Use Timer with immediate execution (0 delay)
                    timer = threading.Timer(
                        0.0, lambda: asyncio.run(send_in_background())
                    )
                    timer.daemon = True
                    timer.start()
                except Exception as e:
                    logger.debug(f"Could not send telemetry event: {e}")

        return wrapper

    return decorator
