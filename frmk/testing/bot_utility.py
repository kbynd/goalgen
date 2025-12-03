#!/usr/bin/env python3
"""
Bot Server Testing Utility

Reusable utility for testing generated Teams bots with Bot Framework Emulator.
Provides CLI interface for starting bot server, sending test messages, and analyzing traces.

Usage:
    # Start bot server
    python test_bot_utility.py start --bot-dir ./teams_app

    # Send test message
    python test_bot_utility.py send --message "Hello" --bot-url http://localhost:3978

    # Analyze traces
    python test_bot_utility.py traces --log-file bot.log

    # Run health check
    python test_bot_utility.py health --bot-url http://localhost:3978
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import httpx


class BotTester:
    """Utility for testing Teams bots"""

    def __init__(self, bot_dir: str, bot_url: str = "http://localhost:3978"):
        self.bot_dir = Path(bot_dir)
        self.bot_url = bot_url
        self.process: Optional[subprocess.Popen] = None

    def start_bot_server(self, background: bool = True) -> subprocess.Popen:
        """Start the bot server"""
        server_path = self.bot_dir / "server.py"

        if not server_path.exists():
            raise FileNotFoundError(f"Bot server not found: {server_path}")

        print(f"Starting bot server from {server_path}...")

        if background:
            self.process = subprocess.Popen(
                [sys.executable, str(server_path)],
                cwd=str(self.bot_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"Bot server started (PID: {self.process.pid})")
            time.sleep(2)  # Wait for server to start
            return self.process
        else:
            # Run in foreground
            subprocess.run(
                [sys.executable, str(server_path)],
                cwd=str(self.bot_dir)
            )

    def stop_bot_server(self):
        """Stop the bot server"""
        if self.process:
            print(f"Stopping bot server (PID: {self.process.pid})...")
            self.process.terminate()
            self.process.wait()
            print("Bot server stopped")

    async def health_check(self) -> Dict[str, Any]:
        """Check bot server health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.bot_url}/health", timeout=5.0)
                response.raise_for_status()
                data = response.json()
                print(f"✅ Bot server is healthy: {data}")
                return data
        except httpx.HTTPError as e:
            print(f"❌ Bot server health check failed: {e}")
            raise

    async def send_message(
        self,
        message: str,
        conversation_id: str = "test-conversation",
        user_id: str = "test-user",
        user_name: str = "Test User"
    ) -> Dict[str, Any]:
        """Send a test message to the bot"""
        activity = {
            "type": "message",
            "id": f"test-message-{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "channelId": "emulator",
            "from": {
                "id": user_id,
                "name": user_name
            },
            "conversation": {
                "id": conversation_id
            },
            "recipient": {
                "id": "bot",
                "name": "Bot"
            },
            "text": message,
            "serviceUrl": "http://localhost"
        }

        print(f"Sending message: '{message}'...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.bot_url}/api/messages",
                    json=activity
                )
                response.raise_for_status()
                data = response.json() if response.content else {}
                print(f"✅ Message sent successfully")
                print(f"Response: {json.dumps(data, indent=2)}")
                return data
        except httpx.HTTPError as e:
            print(f"❌ Failed to send message: {e}")
            raise

    def analyze_traces(self, log_file: Optional[str] = None):
        """Analyze trace logs"""
        if log_file:
            # Read from file
            with open(log_file, 'r') as f:
                lines = f.readlines()
        elif self.process:
            # Read from running process
            if self.process.stderr:
                lines = self.process.stderr.readlines()
            else:
                print("No logs available")
                return
        else:
            print("No log source available. Provide --log-file or start bot server first.")
            return

        # Parse traces
        traces = []
        for line in lines:
            if '[TRACE]' in line:
                traces.append(line.strip())

        if not traces:
            print("No traces found in logs")
            return

        print(f"\n📊 Found {len(traces)} trace entries:\n")

        # Group by trace_id
        trace_groups = {}
        for trace in traces:
            # Extract trace_id
            if 'trace_id=' in trace:
                trace_id = trace.split('trace_id=')[1].split('|')[0].strip()
                if trace_id not in trace_groups:
                    trace_groups[trace_id] = []
                trace_groups[trace_id].append(trace)

        # Print grouped traces
        for trace_id, group in trace_groups.items():
            print(f"Trace ID: {trace_id}")
            print("=" * 80)
            for trace in group:
                print(f"  {trace}")
            print()

        # Calculate total time
        total_times = []
        for group in trace_groups.values():
            for trace in group:
                if 'duration=' in trace:
                    duration_str = trace.split('duration=')[1].split('ms')[0]
                    try:
                        duration = float(duration_str)
                        total_times.append(duration)
                    except ValueError:
                        pass

        if total_times:
            print(f"📈 Performance Summary:")
            print(f"  Total traces: {len(total_times)}")
            print(f"  Min duration: {min(total_times):.2f}ms")
            print(f"  Max duration: {max(total_times):.2f}ms")
            print(f"  Avg duration: {sum(total_times) / len(total_times):.2f}ms")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Bot Server Testing Utility"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start bot server")
    start_parser.add_argument(
        "--bot-dir",
        required=True,
        help="Path to bot directory (e.g., ./teams_app)"
    )
    start_parser.add_argument(
        "--background",
        action="store_true",
        default=True,
        help="Run in background"
    )

    # Send command
    send_parser = subparsers.add_parser("send", help="Send test message")
    send_parser.add_argument(
        "--message",
        required=True,
        help="Message to send"
    )
    send_parser.add_argument(
        "--bot-url",
        default="http://localhost:3978",
        help="Bot server URL"
    )
    send_parser.add_argument(
        "--conversation-id",
        default="test-conversation",
        help="Conversation ID"
    )

    # Health command
    health_parser = subparsers.add_parser("health", help="Check bot health")
    health_parser.add_argument(
        "--bot-url",
        default="http://localhost:3978",
        help="Bot server URL"
    )

    # Traces command
    traces_parser = subparsers.add_parser("traces", help="Analyze trace logs")
    traces_parser.add_argument(
        "--log-file",
        help="Path to log file to analyze"
    )
    traces_parser.add_argument(
        "--bot-dir",
        help="Bot directory (to read from running process)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == "start":
        tester = BotTester(args.bot_dir)
        tester.start_bot_server(background=args.background)
        print(f"\nBot server running on http://localhost:3978")
        print(f"Connect Bot Framework Emulator to: http://localhost:3978/api/messages")
        print("\nPress Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            tester.stop_bot_server()

    elif args.command == "send":
        tester = BotTester(".", bot_url=args.bot_url)
        await tester.send_message(
            message=args.message,
            conversation_id=args.conversation_id
        )

    elif args.command == "health":
        tester = BotTester(".", bot_url=args.bot_url)
        await tester.health_check()

    elif args.command == "traces":
        bot_dir = args.bot_dir or "."
        tester = BotTester(bot_dir)
        tester.analyze_traces(log_file=args.log_file)


if __name__ == "__main__":
    asyncio.run(main())
