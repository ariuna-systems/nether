import asyncio
import pytest
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from typing import Any

from nether.mediator import Mediator, Context
from nether.component import Component
from nether.message import Message, Command, Query, Event


# Test Messages
@dataclass(frozen=True, kw_only=True, slots=True)
class TestCommand(Command):
  value: int


@dataclass(frozen=True, kw_only=True, slots=True)
class TestQuery(Query):
  value: int


@dataclass(frozen=True, kw_only=True, slots=True)
class TestEvent(Event):
  value: int


@dataclass(frozen=True, kw_only=True, slots=True)
class UnhandledMessage(Command):
  value: int


# Test Components
class TestCommandHandler(Component[TestCommand]):
  def __init__(self, application=None):
    super().__init__(application)
    self.handled_messages = []

  async def handle(
    self,
    message: TestCommand,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    self.handled_messages.append(message)


class TestEventHandler(Component[TestEvent]):
  def __init__(self, application=None):
    super().__init__(application)
    self.handled_messages = []

  async def handle(
    self,
    message: TestEvent,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    self.handled_messages.append(message)


class TestMultiMessageHandler(Component[tuple[TestCommand, TestEvent]]):
  def __init__(self, application=None):
    super().__init__(application)
    self.handled_messages = []

  async def handle(
    self,
    message: TestCommand | TestEvent,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    self.handled_messages.append(message)


class EventProducingHandler(Component[TestCommand]):
  def __init__(self, application=None):
    super().__init__(application)
    self.handled_messages = []

  async def handle(
    self,
    message: TestCommand,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    self.handled_messages.append(message)
    # Produce an event when handling command
    await dispatch(TestEvent(value=message.value * 2))


@pytest.fixture
def mediator():
  return Mediator()


@pytest.fixture
def command_handler():
  return TestCommandHandler()


@pytest.fixture
def event_handler():
  return TestEventHandler()


@pytest.fixture
def multi_handler():
  return TestMultiMessageHandler()


@pytest.fixture
def producing_handler():
  return EventProducingHandler()


class TestMediatorBasics:
  """Test basic mediator functionality"""

  def test_mediator_is_singleton(self):
    """Test that Mediator returns the same instance"""
    mediator1 = Mediator()
    mediator2 = Mediator()
    assert mediator1 is mediator2

  def test_attach_component(self, mediator, command_handler):
    """Test attaching a component to mediator"""
    mediator.attach(command_handler)
    assert command_handler in mediator.components

  def test_detach_component(self, mediator, command_handler):
    """Test detaching a component from mediator"""
    mediator.attach(command_handler)
    mediator.detach(command_handler)
    assert command_handler not in mediator.components


class TestMessageHandling:
  """Test message handling functionality"""

  @pytest.mark.asyncio
  async def test_command_routing(self, mediator, command_handler):
    """Test that commands are routed to correct handlers"""
    mediator.attach(command_handler)

    message = TestCommand(value=42)
    await mediator.handle(message)

    # Small delay to ensure async handling completes
    await asyncio.sleep(0.01)

    assert len(command_handler.handled_messages) == 1
    assert command_handler.handled_messages[0] == message

  @pytest.mark.asyncio
  async def test_event_routing(self, mediator, event_handler):
    """Test that events are routed to correct handlers"""
    mediator.attach(event_handler)

    message = TestEvent(value=123)
    await mediator.handle(message)

    await asyncio.sleep(0.01)

    assert len(event_handler.handled_messages) == 1
    assert event_handler.handled_messages[0] == message

  @pytest.mark.asyncio
  async def test_multiple_handlers_same_message(self, mediator, command_handler, multi_handler):
    """Test that multiple handlers can handle the same message type"""
    mediator.attach(command_handler)
    mediator.attach(multi_handler)

    message = TestCommand(value=99)
    await mediator.handle(message)

    await asyncio.sleep(0.01)

    assert len(command_handler.handled_messages) == 1
    assert len(multi_handler.handled_messages) == 1
    assert command_handler.handled_messages[0] == message
    assert multi_handler.handled_messages[0] == message

  @pytest.mark.asyncio
  async def test_multi_message_handler(self, mediator, multi_handler):
    """Test handler that supports multiple message types"""
    mediator.attach(multi_handler)

    command = TestCommand(value=1)
    event = TestEvent(value=2)

    await mediator.handle(command)
    await mediator.handle(event)

    await asyncio.sleep(0.01)

    assert len(multi_handler.handled_messages) == 2
    assert command in multi_handler.handled_messages
    assert event in multi_handler.handled_messages


class TestContextManagement:
  """Test context and unit-of-work functionality"""

  @pytest.mark.asyncio
  async def test_context_creation(self, mediator):
    """Test creating and using a context"""
    async with mediator.context() as ctx:
      assert isinstance(ctx, Context)
      assert ctx.identifier is not None

  @pytest.mark.asyncio
  async def test_context_message_processing(self, mediator, command_handler):
    """Test processing messages through a context"""
    mediator.attach(command_handler)

    async with mediator.context() as ctx:
      message = TestCommand(value=777)
      await ctx.process(message)

    await asyncio.sleep(0.01)

    assert len(command_handler.handled_messages) == 1
    assert command_handler.handled_messages[0] == message

  @pytest.mark.asyncio
  async def test_event_results_queue(self, mediator, event_handler):
    """Test that events are added to context results queue"""
    mediator.attach(event_handler)

    async with mediator.context() as ctx:
      event = TestEvent(value=888)
      await ctx.process(event)

      # Get the result from the queue
      result = await ctx.receive_result()
      assert result == event


class TestEventProduction:
  """Test event production and cascading message handling"""

  @pytest.mark.asyncio
  async def test_handler_produces_events(self, mediator, producing_handler, event_handler):
    """Test that handlers can produce events that are handled by other handlers"""
    mediator.attach(producing_handler)
    mediator.attach(event_handler)

    command = TestCommand(value=10)
    await mediator.handle(command)

    await asyncio.sleep(0.01)

    # Command handler should have processed the command
    assert len(producing_handler.handled_messages) == 1
    assert producing_handler.handled_messages[0] == command

    # Event handler should have processed the produced event
    assert len(event_handler.handled_messages) == 1
    assert event_handler.handled_messages[0].value == 20  # value * 2


class TestErrorHandling:
  """Test error handling and edge cases"""

  @pytest.mark.asyncio
  async def test_unhandled_message_logs_error(self, mediator, caplog):
    """Test that unhandled messages log critical errors"""
    import logging

    with caplog.at_level(logging.CRITICAL):
      message = UnhandledMessage(value=404)
      await mediator.handle(message)

    assert "Handler not found for message" in caplog.text

  @pytest.mark.asyncio
  async def test_handler_exception_handling(self, mediator, caplog):
    """Test that handler exceptions are caught and logged"""
    import logging

    class FailingHandler(Component[TestCommand]):
      def __init__(self, application=None):
        super().__init__(application)

      async def handle(self, message, *, dispatch, join_stream):
        raise ValueError("Test exception")

    failing_handler = FailingHandler()
    mediator.attach(failing_handler)

    with caplog.at_level(logging.CRITICAL):
      await mediator.handle(TestCommand(value=1))
      await asyncio.sleep(0.01)

    assert "Uncaught error" in caplog.text
    assert "Test exception" in caplog.text


class TestMediatorShutdown:
  """Test mediator shutdown and cleanup"""

  @pytest.mark.asyncio
  async def test_mediator_stop(self, mediator, command_handler):
    """Test mediator stop functionality"""
    mediator.attach(command_handler)

    await mediator.stop()

    # After stop, components should be cleared
    # Note: This might reset the singleton, so create a new one
    new_mediator = Mediator()
    assert len(new_mediator.components) == 0


# Cleanup fixture to reset mediator singleton between tests
@pytest.fixture(autouse=True)
async def cleanup_mediator():
  """Reset mediator singleton between tests"""
  yield
  # Reset the singleton instance
  if hasattr(Mediator, "_instance"):
    mediator = Mediator._instance
    if mediator is not None:
      await mediator.stop()
      Mediator._instance = None
