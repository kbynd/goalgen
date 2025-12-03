"""
Distributed Tracing for GoalGen Workflows

Provides simple tracing with timing across the conversation chain.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any
from functools import wraps
from contextvars import ContextVar

# Context variable to track trace_id across async calls
_trace_context: ContextVar[Optional[str]] = ContextVar('trace_context', default=None)
_span_stack: ContextVar[list] = ContextVar('span_stack', default=[])

logger = logging.getLogger(__name__)


class TraceSpan:
    """Represents a traced span of execution"""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time = None
        self.duration_ms = None
        self.metadata: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the span"""
        self.metadata[key] = value

    def end(self):
        """End the span and calculate duration"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }

    def log(self):
        """Log the span"""
        import sys
        # Print directly to stderr for visibility
        print(
            f"[TRACE] {self.name} | "
            f"trace_id={self.trace_id} | "
            f"span_id={self.span_id} | "
            f"duration={self.duration_ms:.2f}ms"
            + (f" | {self.metadata}" if self.metadata else ""),
            file=sys.stderr
        )
        # Also log with logger
        logger.info(
            f"[TRACE] {self.name} | "
            f"trace_id={self.trace_id} | "
            f"span_id={self.span_id} | "
            f"duration={self.duration_ms:.2f}ms"
            + (f" | {self.metadata}" if self.metadata else "")
        )


def start_trace(trace_id: Optional[str] = None) -> str:
    """Start a new trace"""
    if trace_id is None:
        trace_id = uuid.uuid4().hex[:16]
    _trace_context.set(trace_id)
    _span_stack.set([])
    return trace_id


def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return _trace_context.get()


def trace_span(name: str, **metadata):
    """Decorator to trace a function execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get or create trace ID
            trace_id = get_trace_id()
            if trace_id is None:
                trace_id = start_trace()

            # Get parent span
            span_stack = _span_stack.get()
            parent_span_id = span_stack[-1].span_id if span_stack else None

            # Create span
            span = TraceSpan(name, trace_id, parent_span_id)
            for key, value in metadata.items():
                span.add_metadata(key, value)

            # Push to stack
            span_stack.append(span)
            _span_stack.set(span_stack)

            try:
                result = await func(*args, **kwargs)
                span.end()
                span.log()
                return result
            except Exception as e:
                span.end()
                span.add_metadata("error", str(e))
                span.log()
                raise
            finally:
                # Pop from stack
                span_stack.pop()
                _span_stack.set(span_stack)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get or create trace ID
            trace_id = get_trace_id()
            if trace_id is None:
                trace_id = start_trace()

            # Get parent span
            span_stack = _span_stack.get()
            parent_span_id = span_stack[-1].span_id if span_stack else None

            # Create span
            span = TraceSpan(name, trace_id, parent_span_id)
            for key, value in metadata.items():
                span.add_metadata(key, value)

            # Push to stack
            span_stack.append(span)
            _span_stack.set(span_stack)

            try:
                result = func(*args, **kwargs)
                span.end()
                span.log()
                return result
            except Exception as e:
                span.end()
                span.add_metadata("error", str(e))
                span.log()
                raise
            finally:
                # Pop from stack
                span_stack.pop()
                _span_stack.set(span_stack)

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_trace_metadata(key: str, value: Any):
    """Add metadata to the current span"""
    span_stack = _span_stack.get()
    if span_stack:
        span_stack[-1].add_metadata(key, value)
