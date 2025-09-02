import datetime
import time
import logging
import asyncio
from typing import Any, Dict, Optional, Callable
from functools import wraps
import httpx

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
        error: Optional[str] = None,
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
            "request_duration_ms": self.duration_ms,
            "status_code": self.get_status_code(self.success, self.error),
            "error_message": self.error,
            "custom_metrics": self.custom_metrics,
            "timestamp": self.timestamp.isoformat(),
        }


class EventTracker:
    """Handles tool event tracking and sending."""

    def __init__(
        self,
        endpoint_url: str,
        timeout: float = 5.0,
        max_retries: int = 2,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.client = httpx.AsyncClient()
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = headers or {}

    async def send_event(self, event: ToolEvent):
        """Send the event to the event tracking endpoint asynchronously."""
        try:
            payload = event.to_payload()
            headers = {"Content-Type": "application/json", **self.headers}

            for attempt in range(self.max_retries + 1):
                try:
                    response = await self.client.post(
                        self.endpoint_url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout,
                    )
                    logger.debug(
                        f"Event sent successfully: {event.tool_name}.{event.method_name}"
                    )
                    response.raise_for_status()
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
        except Exception as e:
            logger.error(f"Unexpected error sending event: {e}")


# Global event tracker instance
_event_tracker: Optional[EventTracker] = None


def create_event_tracker(
    base_url: Optional[str] = None,
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

    # Create new tracker if base_url provided
    if base_url:
        endpoint_url = base_url.rstrip("/") + "/tool/event"
        _event_tracker = EventTracker(
            endpoint_url=endpoint_url,
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
        )
        return _event_tracker

    # No existing tracker and no base_url provided
    return None


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

                # Handle async send_event call
                try:
                    # Check if we're already in an event loop
                    asyncio.get_running_loop()
                    # If we're already in an event loop, create a task
                    asyncio.create_task(tracker.send_event(event))
                except RuntimeError:
                    # No event loop is running, create a new one
                    asyncio.run(tracker.send_event(event))

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
                error = str(e)
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

                # For async functions, fire-and-forget the event tracking
                asyncio.create_task(tracker.send_event(event))

        return wrapper

    return decorator
