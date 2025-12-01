"""
WebSocket-based Tool Implementation
For real-time services on Container Apps
"""

from typing import Dict, Any, Optional, AsyncIterator
import websockets
import json
import asyncio
from .base_tool import BaseTool, ToolOutput
from frmk.utils.logging import get_logger


class WebSocketTool(BaseTool):
    """
    WebSocket-based tool for real-time services

    Configuration from spec:
    {
      "type": "websocket",
      "spec": {
        "url": "wss://realtime-service.azurecontainerapps.io/ws",
        "auth": "bearer",
        "reconnect": true,
        "reconnect_interval": 5,
        "heartbeat_interval": 30
      }
    }
    """

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        super().__init__(name, description, tool_config)

        self.logger = get_logger(f"tool.{name}")

        spec = tool_config.get("spec", {})

        self.url = spec.get("url", "")
        self.auth_type = spec.get("auth", None)
        self.reconnect = spec.get("reconnect", True)
        self.reconnect_interval = spec.get("reconnect_interval", 5)
        self.heartbeat_interval = spec.get("heartbeat_interval", 30)

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connection_lock = asyncio.Lock()

    async def _connect(self):
        """Establish WebSocket connection"""

        if self.websocket and not self.websocket.closed:
            return

        async with self._connection_lock:
            # Double-check after acquiring lock
            if self.websocket and not self.websocket.closed:
                return

            headers = {}

            # Add auth if configured
            if self.auth_type == "bearer":
                import os
                token = os.getenv(f"{self.name.upper()}_TOKEN")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            try:
                self.websocket = await websockets.connect(
                    self.url,
                    extra_headers=headers,
                    ping_interval=self.heartbeat_interval,
                    ping_timeout=10,
                )

                self.logger.info(f"WebSocket connected: {self.url}")

            except Exception as e:
                self.logger.error(f"WebSocket connection failed: {e}")
                raise

    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute WebSocket tool call (request-response)

        Args:
            **kwargs: Message payload to send

        Returns:
            ToolOutput with response
        """

        try:
            # Ensure connection
            await self._connect()

            # Send message
            message = json.dumps(kwargs)
            await self.websocket.send(message)

            self.logger.debug(f"Sent WebSocket message: {message}")

            # Wait for response
            response_text = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=30
            )

            response_data = json.loads(response_text)

            return ToolOutput(
                success=True,
                data=response_data,
                metadata={"protocol": "websocket"}
            )

        except asyncio.TimeoutError:
            self.logger.error("WebSocket response timeout")
            return ToolOutput(
                success=False,
                error="Response timeout"
            )

        except websockets.ConnectionClosed as e:
            self.logger.error(f"WebSocket connection closed: {e}")

            # Try to reconnect if configured
            if self.reconnect:
                self.websocket = None
                await asyncio.sleep(self.reconnect_interval)
                return await self.execute(**kwargs)  # Retry

            return ToolOutput(
                success=False,
                error="Connection closed"
            )

        except Exception as e:
            self.logger.error(f"WebSocket execution failed: {e}")
            return ToolOutput(
                success=False,
                error=str(e)
            )

    async def stream(self, **kwargs) -> AsyncIterator[ToolOutput]:
        """
        Execute WebSocket tool call with streaming response

        Args:
            **kwargs: Message payload to send

        Yields:
            ToolOutput for each message received
        """

        try:
            await self._connect()

            # Send initial message
            message = json.dumps(kwargs)
            await self.websocket.send(message)

            # Stream responses
            async for response_text in self.websocket:
                response_data = json.loads(response_text)

                yield ToolOutput(
                    success=True,
                    data=response_data,
                    metadata={"protocol": "websocket", "streaming": True}
                )

                # Check for end-of-stream marker
                if response_data.get("_stream_end"):
                    break

        except Exception as e:
            self.logger.error(f"WebSocket streaming failed: {e}")
            yield ToolOutput(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for WebSocket message"""

        if "input_schema" in self.config.get("spec", {}):
            return self.config["spec"]["input_schema"]

        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": f"Message to send to {self.name}"
                }
            },
            "required": ["message"]
        }

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")
