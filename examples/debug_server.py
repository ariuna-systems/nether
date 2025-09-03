#!/usr/bin/env python3
"""
Debug server example for testing enhanced 404 debugging capabilities.

Usage:
    python debug_server.py --log-level DEBUG

This will start a server with comprehensive debug logging that will help
you understand why 404 errors occur.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from aiohttp import web

# Add the src directory to the path so we can import nether
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import nether
from nether.logging import configure_global_logging
from nether.server import Server


class DebugSystem(nether.Nether):
    """Simple system for debugging HTTP server capabilities."""

    async def main(self) -> None:
        """Main application setup - just keep running."""
        print("Debug system started and ready for requests...")


class HelloView(web.View):
    async def get(self):
        return web.Response(text="Hello, World!")


class ApiView(web.View):
    async def get(self):
        return web.json_response({"message": "API endpoint", "status": "ok"})

    async def post(self):
        return web.json_response({"message": "Data received", "method": "POST"})


async def main():
    parser = argparse.ArgumentParser(description="Debug Server Example")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )

    args = parser.parse_args()

    # Configure global logging
    configure_global_logging(log_level=args.log_level)

    # Create system and server
    app = DebugSystem(configuration=args)
    server = Server(app, configuration=args)
    app.attach(server)

    print(f"Starting debug server with log level: {args.log_level}")
    print(f"Server will be available at: http://{args.host}:{args.port}")
    print()
    print("Available routes after startup:")
    print("  GET  /hello       - Simple hello world")
    print("  GET  /api         - JSON API endpoint")
    print("  POST /api         - JSON API endpoint (accepts POST)")
    print("  GET  /static/*    - Static files from ./static/")
    print()
    print("Try accessing non-existent routes to see debug output:")
    print("  GET  /nonexistent")
    print("  GET  /api/v1/users")
    print("  POST /hello")
    print()

    # Start the application
    await app.start()

    # Register routes
    from nether.message import Message
    from nether.server import AddStatic, RegisterView

    # Register views
    hello_msg = RegisterView(route="/hello", view=HelloView)
    api_msg = RegisterView(route="/api", view=ApiView)

    # Register static files (create a static directory if it doesn't exist)
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)

    # Create a simple static file for testing
    (static_dir / "test.txt").write_text("This is a static file for testing")

    static_msg = AddStatic(prefix="/static", path=static_dir)

    # Handle the messages
    async def handler(message: Message) -> None:
        print(f"Event: {type(message).__name__}")

    await server.handle(hello_msg, handler=handler)
    await server.handle(api_msg, handler=handler)
    await server.handle(static_msg, handler=handler)

    print("Server is running. Press Ctrl+C to stop.")

    try:
        # Keep the server running
        shutdown_event = asyncio.Event()
        await shutdown_event.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
