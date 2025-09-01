# Testing the Nether Mediator

## Overview

The Mediator is the core component of the Nether framework that routes messages between components asynchronously. Here's how to test it comprehensively:

## Test Categories

### 1. Basic Mediator Functionality

- **Singleton Pattern**: Verify mediator returns same instance
- **Component Management**: Test attach/detach of components
- **Component Discovery**: Verify components are found in mediator.components

### 2. Message Routing

- **Single Handler**: Test message routed to correct handler
- **Multiple Handlers**: Test same message type handled by multiple components
- **Multi-Message Handlers**: Test components that handle multiple message types
- **Unhandled Messages**: Test error logging for messages with no handlers

### 3. Context Management

- **Context Creation**: Test context manager functionality
- **Message Processing**: Test ctx.process() routes messages correctly
- **Event Results**: Test events are queued in context results
- **Task Management**: Test active tasks are tracked and cleaned up

### 4. Asynchronous Behavior

- **Concurrent Handling**: Test multiple messages processed concurrently
- **Event Production**: Test handlers that produce events for other handlers
- **Task Isolation**: Test each context has isolated task management

### 5. Error Handling

- **Handler Exceptions**: Test exceptions in handlers are caught and logged
- **Invalid Messages**: Test non-Message objects are rejected
- **Context Cleanup**: Test contexts clean up even with errors

### 6. Lifecycle Management

- **Component Lifecycle**: Test on_start/on_stop called correctly
- **Mediator Shutdown**: Test mediator.stop() cleans up properly
- **Singleton Reset**: Test singleton can be reset for testing

## Running Tests

```bash
# Run all mediator tests
pytest tests/mediator_test.py -v

# Run specific test class
pytest tests/mediator_test.py::TestMessageHandling -v

# Run with async support and output
pytest tests/mediator_test.py -v -s --asyncio-mode=auto
```

## Test Patterns

### Creating Test Components

```python
class TestHandler(Component[YourMessageType]):
    def __init__(self, application=None):
        super().__init__(application)
        self.handled_messages = []
        
    async def handle(self, message, *, dispatch, join_stream):
        self.handled_messages.append(message)
        # Optionally dispatch new messages
        await dispatch(AnotherMessage())
```

### Testing Message Flow

```python
@pytest.mark.asyncio
async def test_message_routing():
    mediator = Mediator()
    handler = TestHandler()
    mediator.attach(handler)
    
    message = TestMessage(value=42)
    await mediator.handle(message)
    
    # Allow async processing to complete
    await asyncio.sleep(0.01)
    
    assert len(handler.handled_messages) == 1
    assert handler.handled_messages[0] == message
```

### Testing Context Usage

```python
@pytest.mark.asyncio
async def test_context_processing():
    mediator = Mediator()
    handler = TestHandler()
    mediator.attach(handler)
    
    async with mediator.context() as ctx:
        await ctx.process(TestMessage(value=123))
        
        # For events, can retrieve from results
        if isinstance(message, Event):
            result = await ctx.receive_result()
            assert result == message
```

### Testing Event Production

```python
class EventProducer(Component[Command]):
    async def handle(self, message, *, dispatch, join_stream):
        # Process command and produce event
        await dispatch(ResultEvent(value=message.value * 2))

@pytest.mark.asyncio        
async def test_event_cascading():
    mediator = Mediator()
    producer = EventProducer()
    consumer = EventConsumer()
    
    mediator.attach(producer)
    mediator.attach(consumer)
    
    await mediator.handle(TestCommand(value=10))
    await asyncio.sleep(0.01)
    
    # Check both command processed and event produced
    assert len(consumer.handled_events) == 1
    assert consumer.handled_events[0].value == 20
```

## Key Testing Considerations

1. **Async Delays**: Always add small delays (`await asyncio.sleep(0.01)`) after mediator.handle() to allow async processing to complete

2. **Singleton Reset**: Reset the mediator singleton between tests to avoid test interference

3. **Error Logging**: Use `caplog` fixture to test error logging behavior

4. **Component Types**: Test components with different message type specifications (single type, tuple of types)

5. **Context Isolation**: Verify each context maintains its own task queue and results

6. **Memory Leaks**: Ensure tasks are properly cleaned up and don't accumulate

The comprehensive test suite covers all these aspects and provides a solid foundation for testing mediator functionality.
