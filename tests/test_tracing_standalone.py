"""
Standalone unit tests for frmk/utils/tracing.py

Tests the tracing module without importing the full frmk package
to avoid heavy Azure SDK dependencies during testing.
"""

import pytest
import asyncio
import time
import os
from unittest.mock import patch
import sys
import importlib.util

# Load tracing module directly without going through frmk package
spec = importlib.util.spec_from_file_location(
    "tracing",
    os.path.join(os.path.dirname(__file__), "../frmk/utils/tracing.py")
)
tracing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracing)

# Extract what we need from the module
TraceSpan = tracing.TraceSpan
start_trace = tracing.start_trace
get_trace_id = tracing.get_trace_id
trace_span = tracing.trace_span
TRACING_ENABLED = tracing.TRACING_ENABLED


class TestTraceSpan:
    """Test TraceSpan class for measuring execution timing"""

    def test_trace_span_creation(self):
        """Test TraceSpan can be created with name and trace_id"""
        span = TraceSpan("test.operation", "trace-123")

        assert span.name == "test.operation"
        assert span.trace_id == "trace-123"
        assert span.metadata == {}
        assert span.start_time > 0
        assert span.end_time is None

    def test_trace_span_timing(self):
        """Test TraceSpan measures execution time correctly"""
        span = TraceSpan("test.sleep", "trace-456")

        # Simulate some work
        time.sleep(0.05)  # 50ms
        span.end()

        duration = span.duration_ms  # Property, not method
        assert duration >= 50.0  # At least 50ms
        assert duration < 100.0  # But less than 100ms (reasonable upper bound)

    def test_trace_span_metadata(self):
        """Test TraceSpan can store metadata"""
        span = TraceSpan("test.metadata", "trace-789")
        span.add_metadata("user_id", "user-123")
        span.add_metadata("action", "create")

        assert span.metadata["user_id"] == "user-123"
        assert span.metadata["action"] == "create"

    def test_trace_span_log_output(self, capsys):
        """Test TraceSpan.log() outputs correct format"""
        span = TraceSpan("test.log", "trace-abc")
        span.add_metadata("component", "api")
        time.sleep(0.01)  # 10ms
        span.end()
        span.log()

        captured = capsys.readouterr()
        # Logging uses logger.info which goes to stderr in pytest
        output = captured.err
        assert "TRACE" in output
        assert "test.log" in output
        assert "trace-abc" in output
        assert "component" in output
        assert "api" in output
        assert "ms" in output


class TestTraceIDPropagation:
    """Test trace ID context propagation"""

    def test_start_trace_creates_new_id(self):
        """Test start_trace() creates a new trace_id"""
        trace_id = start_trace()

        assert trace_id is not None
        assert isinstance(trace_id, str)
        assert len(trace_id) > 0

    def test_start_trace_accepts_existing_id(self):
        """Test start_trace() can accept an existing trace_id"""
        existing_id = "external-trace-123"
        trace_id = start_trace(existing_id)

        assert trace_id == existing_id

    def test_get_trace_id_returns_current(self):
        """Test get_trace_id() returns current context trace_id"""
        # Start a new trace
        original_id = start_trace("my-trace-id")

        # Get should return the same ID
        retrieved_id = get_trace_id()
        assert retrieved_id == "my-trace-id"


class TestTracingConfiguration:
    """Test TRACING_ENABLED configuration"""

    def test_tracing_enabled_is_boolean(self):
        """Test TRACING_ENABLED is a boolean value"""
        assert isinstance(TRACING_ENABLED, bool)


class TestTraceSpanDecorator:
    """Test @trace_span decorator functionality"""

    @pytest.mark.asyncio
    async def test_decorator_on_async_function(self, capsys):
        """Test decorator works on async functions"""

        @trace_span("test.async_decorated")
        async def async_operation(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        result = await async_operation(5)

        assert result == 10

        # Check trace output (logging goes to stderr)
        captured = capsys.readouterr()
        assert "test.async_decorated" in captured.err

    def test_decorator_on_sync_function(self, capsys):
        """Test decorator works on sync functions"""

        @trace_span("test.sync_decorated")
        def sync_operation(x: int) -> int:
            time.sleep(0.01)
            return x + 10

        result = sync_operation(5)

        assert result == 15

        # Check trace output (logging goes to stderr)
        captured = capsys.readouterr()
        assert "test.sync_decorated" in captured.err

    @pytest.mark.asyncio
    async def test_decorator_with_metadata(self, capsys):
        """Test decorator accepts metadata kwargs"""

        @trace_span("test.with_metadata", component="api", version="1.0")
        async def operation_with_meta():
            return "done"

        result = await operation_with_meta()

        assert result == "done"

        captured = capsys.readouterr()
        output = captured.err
        assert "component" in output
        assert "api" in output
        assert "version" in output
        assert "1.0" in output

    @pytest.mark.asyncio
    async def test_decorator_propagates_exceptions(self):
        """Test decorator re-raises exceptions from decorated functions"""

        @trace_span("test.exception")
        async def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_operation()

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function name and docstring"""

        @trace_span("test.preserved")
        async def documented_function(x: int) -> int:
            """This function has documentation"""
            return x

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This function has documentation"


class TestIntegration:
    """Integration tests showing full tracing workflow"""

    @pytest.mark.asyncio
    async def test_distributed_trace_simulation(self, capsys):
        """Test simulating distributed trace across multiple services"""

        # Service 1: Bot creates trace
        trace_id = start_trace()

        @trace_span("bot.on_message_activity")
        async def bot_handler(message: str):
            span = TraceSpan("bot.call_api", trace_id)
            span.add_metadata("component", "teams_bot")
            await asyncio.sleep(0.01)
            span.end()
            span.log()
            return trace_id  # Simulate sending via HTTP header

        # Service 2: Orchestrator receives trace_id
        @trace_span("orchestrator.send_message")
        async def orchestrator_handler(received_trace_id: str, message: str):
            # Reuse the trace_id from bot
            start_trace(received_trace_id)
            span = TraceSpan("orchestrator.process", received_trace_id)
            span.add_metadata("component", "orchestrator")
            await asyncio.sleep(0.01)
            span.end()
            span.log()
            return "response"

        # Execute distributed trace
        propagated_trace_id = await bot_handler("Hello")
        response = await orchestrator_handler(propagated_trace_id, "Hello")

        assert response == "response"

        # Verify both services logged with same trace_id (logging goes to stderr)
        captured = capsys.readouterr()
        output = captured.err
        assert trace_id in output
        assert "bot.call_api" in output
        assert "orchestrator.process" in output
        assert "teams_bot" in output
        assert "orchestrator" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
