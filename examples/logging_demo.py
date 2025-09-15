#!/usr/bin/env python3
"""
Logging Demo for Nether Framework

This example demonstrates the comprehensive logging capabilities
of the Nether framework with command-line configuration options.

Usage:
    # Basic logging to stdout with INFO level
    python logging_demo.py

    # Enable DEBUG level logging
    python logging_demo.py --log-level DEBUG

    # Log to file as well as stdout
    python logging_demo.py --log-file logs/nether.log

    # Increase verbosity
    python logging_demo.py -v -v

    # Combine options
    python logging_demo.py --log-level DEBUG --log-file logs/app.log -v
"""

import argparse
import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import nether
from nether.modules import Module
from nether.message import Command, Event, Message, Query


@dataclass(frozen=True, slots=True, kw_only=True)
class LogTestCommand(Command):
    """A test command for logging demonstration."""

    message: str
    level: str = "info"


@dataclass(frozen=True, slots=True, kw_only=True)
class LogTestQuery(Query):
    """A test query for logging demonstration."""

    question: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LogTestEvent(Event):
    """A test event for logging demonstration."""

    result: str
    timestamp: str


class LoggingDemoComponent(Module[LogTestCommand | LogTestQuery]):
    """Module that demonstrates various logging scenarios."""

    async def handle(
        self,
        message: LogTestCommand | LogTestQuery,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        """Handle test messages and demonstrate logging."""
        import logging

        logger = logging.getLogger(__name__)

        match message:
            case LogTestCommand():
                level = getattr(logging, message.level.upper(), logging.INFO)
                logger.log(level, f"Processing command: {message.message}")

                # Generate an event as response
                event = LogTestEvent(result=f"Processed: {message.message}", timestamp=datetime.now().isoformat())
                await handler(event)

            case LogTestQuery():
                logger.info(f"Processing query: {message.question}")

                # Simulate some work
                await asyncio.sleep(0.1)

                # Generate an event as response
                event = LogTestEvent(
                    result=f"Answer to '{message.question}': This is a demo response",
                    timestamp=datetime.now().isoformat(),
                )
                await handler(event)


class EventHandler(Module[LogTestEvent]):
    """Module that handles events and logs them."""

    async def handle(
        self,
        message: LogTestEvent,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        """Handle events."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Event received: {message.result} at {message.timestamp}")


class LoggingDemoApp(nether.Nether):
    """Demo application showcasing logging."""

    async def main(self) -> None:
        """Main application logic."""
        import logging

        logger = logging.getLogger(__name__)

        logger.info("=== Nether Logging Demo Started ===")

        # Create and attach components
        demo_component = LoggingDemoComponent(self)
        event_handler = EventHandler(self)

        self.attach(demo_component, event_handler)

        logger.info("Components attached successfully")

        # Demonstrate different types of messages
        test_messages = [
            LogTestCommand(message="This is a test command", level="info"),
            LogTestCommand(message="This is a debug message", level="debug"),
            LogTestCommand(message="This is a warning", level="warning"),
            LogTestQuery(question="What is the meaning of life?"),
            LogTestQuery(question="How does the mediator work?"),
        ]

        logger.info("Starting message processing demonstration...")

        for i, msg in enumerate(test_messages, 1):
            logger.debug(f"Processing message {i}/{len(test_messages)}")

            async with self.mediator.context() as ctx:
                await ctx.process(msg)

            # Small delay between messages for clarity
            await asyncio.sleep(0.2)

        logger.info("All messages processed successfully")
        logger.info("=== Demo completed ===")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Nether Framework Logging Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        help="Path to the log file for file logging (optional)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity level",
    )

    args = parser.parse_args()

    # Create configuration
    config = argparse.Namespace(log_level=args.log_level, log_file=args.log_file, verbose=args.verbose)

    print("=== Nether Framework Logging Demo ===")
    print(f"Log Level: {args.log_level}")
    if args.log_file:
        print(f"Log File: {args.log_file}")
    if args.verbose:
        print(f"Verbosity: {args.verbose}")
    print("=" * 40)

    # Create and run the application
    app = LoggingDemoApp(configuration=config)
    nether.execute(app.start())


if __name__ == "__main__":
    main()
