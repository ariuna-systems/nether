# Actor Model in Nether Framework

## Overview

The **nether framework** implements a sophisticated Actor Model pattern through its `Module` class, enhanced with modern async capabilities and innovative streaming features. While the framework uses "Module" terminology, the underlying architecture follows classic Actor Model principles with significant enhancements.

## Actor Model Fundamentals

The Actor Model is a concurrent computation model where:

- **Actors** are fundamental units of computation
- **Message Passing** is the only form of communication
- **Encapsulation** ensures no shared mutable state
- **Asynchronous Processing** handles messages independently
- **Supervision** manages actor lifecycle and failures

## Module as Actor Implementation

### Core Actor Properties

| **Actor Model Concept** | **Module Implementation** | **Code Evidence** |
|-------------------------|----------------------------|-------------------|
| **Encapsulated State** | Private instance variables | `self._is_running`, `self._logger`, `self.processed_count` |
| **Message Passing** | `handle(message, *, handler, ...)` | Only communicates via messages |
| **No Shared Memory** | Isolated component instances | Each component manages own state |
| **Asynchronous Processing** | `async def handle(...)` | Built on asyncio |
| **Actor Address/Reference** | Message type subscription `Module[T]` | Mediator routes by message type |
| **Supervisor Hierarchy** | `Application` manages components | Lifecycle management |
| **Message Queues** | Mediator queuing system | Messages routed through mediator |

### Actor Definition Pattern

```python
class TemperatureProcessor(Module[StartDataCollection]):  #  Actor
    def __init__(self, application):
        super().__init__(application)
        self.processed_count = 0  #  Private state
        
    async def handle(self, message, *, handler, channel):  #  Message handler
        # Process the message
        temp = self._analyze_temperature(message.data)
        
        # Send messages to other actors (no direct calls)
        if temp > 25.0:
            await handler(TemperatureAlert(temp=temp))  #  Message passing
```

## Enhanced Actor Model Features

### 1. **Type-Safe Message Subscription**

Traditional actor systems use string-based addressing. Nether uses Python's type system:

```python
# Traditional Actor: actor.send("temperature_processor", message)
# Nether Actor: Automatic routing by message type
class TemperatureProcessor(Module[TemperatureReading]):
    async def handle(self, message: TemperatureReading, *, handler, channel):
        # Only receives TemperatureReading messages
```

### 2. **Shared Streaming within Context**

**Innovation**: The `channel` parameter adds shared data streaming capabilities while maintaining Actor isolation:

```python
async def handle(self, message, *, handler, channel):
    # Classic Actor: Isolated message passing
    await handler(SomeMessage())
    
    # Enhanced Actor: Shared data streams within context
    stream_queue, stop_event = channel()  #  Shared stream access
    data = await stream_queue.get()
```

This allows multiple actors to process the same continuous data stream within a single context (unit of work).

### 3. **Context-Isolated Actor Groups**

The `Context` class provides unit-of-work isolation:

```python
async with mediator.context() as ctx:
    # All actors within this context share streams
    # but are isolated from other contexts
    await ctx.process(StartDataCollection())
```

## Practical Actor Examples

### Simple Command Actor

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class ProcessOrder(Command):
    order_id: str
    amount: float

class OrderProcessor(Module[ProcessOrder]):
    def __init__(self, application):
        super().__init__(application)
        self.orders_processed = 0  # Actor state
        
    async def handle(self, message: ProcessOrder, *, handler, channel):
        # Process order logic
        success = await self._process_order(message.order_id, message.amount)
        self.orders_processed += 1
        
        # Send result to other actors
        if success:
            await handler(OrderCompleted(order_id=message.order_id))
        else:
            await handler(OrderFailed(order_id=message.order_id))
```

### Streaming Data Actor

```python
class SensorDataProcessor(Module[StartMonitoring]):
    def __init__(self, application):
        super().__init__(application)
        self.readings_count = 0
        
    async def handle(self, message, *, handler, channel):
        stream_queue, stop_event = channel()
        
        print(" Sensor Actor: Started monitoring")
        
        while not stop_event.is_set():
            try:
                # Receive from shared stream
                sensor_data = await asyncio.wait_for(stream_queue.get(), timeout=1.0)
                
                # Process data
                if sensor_data['temperature'] > 30:
                    await handler(HighTemperatureAlert(
                        temp=sensor_data['temperature']
                    ))
                
                self.readings_count += 1
                
            except asyncio.TimeoutError:
                continue
```

### Multi-Message Type Actor

```python
class SystemMonitor(Module[tuple[SystemStart, SystemStop, HealthCheck]]):
    def __init__(self, application):
        super().__init__(application)
        self.status = "stopped"
        
    async def handle(self, message, *, handler, channel):
        match message:
            case SystemStart():
                self.status = "running"
                await handler(SystemStatusChanged(status="running"))
                
            case SystemStop():
                self.status = "stopped" 
                await handler(SystemStatusChanged(status="stopped"))
                
            case HealthCheck():
                await handler(HealthReport(
                    status=self.status,
                    uptime=self._get_uptime()
                ))
```

## Actor Lifecycle Management

### Application as Actor Supervisor

```python
class MyApplication(Nether):
    async def main(self):
        # Register actors (components) with supervisor
        self.register_component(OrderProcessor(self))
        self.register_component(PaymentProcessor(self))
        self.register_component(NotificationSender(self))
        
        # Start processing
        async with self.mediator.context() as ctx:
            await ctx.process(ProcessOrder(order_id="123", amount=99.99))
```

### Actor States

```python
class ComponentState(StrEnum):
    STARTED = "started"
    PENDING = "pending" 
    RUNNING = "running"
    STOPPED = "stopped"
```

Actors have lifecycle hooks:

- `async def on_start(self)` - Actor initialization
- `async def on_stop(self)` - Actor cleanup
- `async def on_error(self)` - Error handling

## Comparison with Traditional Actor Systems

### Advantages of Nether's Actor Implementation

1. **Type Safety**: Compile-time message type checking via generics
2. **Async Native**: Built on asyncio, not threads or processes
3. **Shared Streaming**: Innovative addition for real-time data processing
4. **Python Idiomatic**: Uses dataclasses, type hints, async/await
5. **Minimal Dependencies**: Lightweight compared to full actor frameworks

### Traditional Actor Systems vs Nether

| **Feature** | **Traditional (e.g., Akka)** | **Nether Components** |
|-------------|------------------------------|----------------------|
| **Message Addressing** | String-based actor paths | Type-based routing |
| **Concurrency** | Thread/process-based | asyncio-based |
| **Message Definition** | Classes/case classes | Python dataclasses |
| **Shared State** | Not allowed | Controlled via streams |
| **Error Handling** | Supervisor strategies | Module lifecycle hooks |
| **Performance** | High for CPU-bound | Optimized for I/O-bound |

## Actor Communication Patterns

### 1. **Fire-and-Forget**

```python
await handler(LogEvent(message="Order processed"))
```

### 2. **Request-Response** (via Events)

```python
# Send command
await handler(ProcessPayment(amount=100))

# Handle response in another actor
class PaymentResultHandler(Module[PaymentCompleted]):
    async def handle(self, message, *, handler, channel):
        print(f"Payment completed: {message.transaction_id}")
```

### 3. **Fan-out Processing**

```python
# Multiple actors process the same stream
async def handle(self, message, *, handler, channel):
    stream_queue, stop_event = channel()
    # TemperatureProcessor, HumidityProcessor, DataAggregator
    # all process the same sensor data stream
```

## Best Practices

### Actor Design Guidelines

1. **Single Responsibility**: Each actor handles one specific concern
2. **Stateful but Isolated**: Maintain internal state, never share it
3. **Message-Only Communication**: No direct method calls between actors
4. **Error Isolation**: Actor failures don't crash other actors
5. **Lifecycle Awareness**: Implement proper start/stop procedures

### Message Design

```python
# Good: Immutable messages with clear intent
@dataclass(frozen=True, kw_only=True, slots=True)
class ProcessOrder(Command):
    order_id: str
    customer_id: str
    items: list[dict]
    
# Good: Events for notifications
@dataclass(frozen=True, kw_only=True, slots=True)
class OrderCompleted(Event):
    order_id: str
    total_amount: float
    timestamp: datetime
```

### Context Usage

```python
# Context provides unit-of-work isolation
async with self.mediator.context() as ctx:
    # All actors in this context share streams
    # but are isolated from other contexts
    await ctx.process(StartWorkflow())
    
    # Wait for completion
    async for event in ctx.results():
        if isinstance(event, WorkflowCompleted):
            break
```

## Conclusion

The nether framework successfully implements a modern, async-first Actor Model through its Module architecture. Key innovations include:

- **Type-safe message routing** via generic type parameters
- **Shared streaming capabilities** within isolated contexts  
- **Python-idiomatic design** using dataclasses and async/await
- **Lightweight implementation** focusing on I/O-bound workloads

While maintaining core Actor principles of encapsulation, message passing, and isolation, nether enhances the pattern with practical features for modern web service development.

The `channel` parameter represents a novel extension to the Actor Model, enabling shared data processing while preserving actor isolation—making it ideal for real-time data processing scenarios.

This design makes nether both a **pure Actor framework** and a **practical web service foundation**, bridging the gap between academic actor models and real-world application needs.
