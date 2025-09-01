#!/usr/bin/env python3
"""
Simple test script to verify Mediator functionality
Run with: python simple_mediator_test.py
"""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

# Add src to path to import nether
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nether.mediator import Mediator
from nether.component import Component
from nether.message import Command, Event


@dataclass(frozen=True, kw_only=True, slots=True)
class TestCommand(Command):
  value: int


@dataclass(frozen=True, kw_only=True, slots=True)
class TestEvent(Event):
  value: int


class TestHandler(Component[TestCommand]):
  def __init__(self):
    super().__init__(application=None)
    self.handled_messages = []

  async def handle(self, message, *, dispatch, join_stream):
    self.handled_messages.append(message)
    print(f"Handler received: {message}")

    # Produce an event
    event = TestEvent(value=message.value * 2)
    await dispatch(event)


class EventHandler(Component[TestEvent]):
  def __init__(self):
    super().__init__(application=None)
    self.handled_events = []

  async def handle(self, message, *, dispatch, join_stream):
    self.handled_events.append(message)
    print(f"Event handler received: {message}")


async def main():
  print("Testing Mediator functionality...")

  # Test 1: Basic singleton
  print("\n1. Testing singleton pattern")
  mediator1 = Mediator()
  mediator2 = Mediator()
  assert mediator1 is mediator2, "Mediator should be singleton"
  print("✓ Singleton test passed")

  # Test 2: Component attachment
  print("\n2. Testing component attachment")
  handler = TestHandler()
  event_handler = EventHandler()

  mediator1.attach(handler)
  mediator1.attach(event_handler)

  assert handler in mediator1.components, "Handler should be attached"
  assert event_handler in mediator1.components, "Event handler should be attached"
  print("✓ Component attachment test passed")

  # Test 3: Message routing
  print("\n3. Testing message routing")
  message = TestCommand(value=42)
  await mediator1.handle(message)

  # Give async processing time to complete
  await asyncio.sleep(0.1)

  assert len(handler.handled_messages) == 1, f"Expected 1 message, got {len(handler.handled_messages)}"
  assert handler.handled_messages[0] == message, "Message should match"
  print("✓ Message routing test passed")

  # Test 4: Event production and cascading
  print("\n4. Testing event production")
  assert len(event_handler.handled_events) == 1, f"Expected 1 event, got {len(event_handler.handled_events)}"
  assert event_handler.handled_events[0].value == 84, f"Expected value 84, got {event_handler.handled_events[0].value}"
  print("✓ Event production test passed")

  # Test 5: Context usage
  print("\n5. Testing context usage")
  async with mediator1.context() as ctx:
    test_message = TestCommand(value=123)
    await ctx.process(test_message)

    # Event should be available in results
    result = await ctx.receive_result()
    assert isinstance(result, TestEvent), f"Expected TestEvent, got {type(result)}"
    assert result.value == 246, f"Expected 246, got {result.value}"

  await asyncio.sleep(0.1)

  assert len(handler.handled_messages) == 2, f"Expected 2 messages total, got {len(handler.handled_messages)}"
  print("✓ Context usage test passed")

  # Test 6: Multiple handlers for same message
  print("\n6. Testing multiple handlers")
  handler2 = TestHandler()
  mediator1.attach(handler2)

  message3 = TestCommand(value=999)
  await mediator1.handle(message3)
  await asyncio.sleep(0.1)

  assert len(handler.handled_messages) == 3, "First handler should have 3 messages"
  assert len(handler2.handled_messages) == 1, "Second handler should have 1 message"
  assert handler2.handled_messages[0] == message3, "Second handler should have received the message"
  print("✓ Multiple handlers test passed")

  # Cleanup
  await mediator1.stop()
  print("\n✅ All tests passed! Mediator is working correctly.")


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
