# Nether

[![Sphinx Docs](https://github.com/arjuna-systems/nether/actions/workflows/docs.yml/badge.svg)](https://github.com/arjuna-systems/nether/actions/workflows/docs.yml)

> Nether means beneath, below, or underneath

Nether is a framework for building **message-driven systems** in Python. 
Originally created to serve internal needs, it may or may not suit your use case&mdash;our goal is not to build a universal framework, but one that works best for us.

**Disclaimer**: Nether is actively under development. While the core architecture is stable, APIs may evolve as we continue to refine the framework based on real-world usage.

Use Nether to build:

- **Reactive systems** that respond to events and scale with demand
- **Streaming systems** for real-time data processing and event handling  

Nether's message-driven design make it particularly well-suited for:

- **Event Sourcing (ES)** - Natural event handling and state reconstruction
- **Domain-Driven Design (DDD)** - Clear bounded contexts and domain isolation
- **Clean Architecture (CA)** - Dependency inversion through message passing
- **Command and Query Segregation (CQRS)** - Separate command and query handling with type safety

## Philosophy

- **Actor Model**: Components communicate only through message passing
- **Async-first**: Built on Python's asyncio for high-performance I/O
- **Minimal dependencies**: Favor standard library over external packages  
- **Fault isolation**: Actor failures don't crash the entire system
- **Graceful operations**: Clean startup, shutdown, and error handling

## Features

- **Message-driven architecture** with Commands, Events, and Queries
- **Actor-based components** with isolated state and async message handling
- **Shared streaming** for real-time data processing within contexts
- **Type-safe message routing** using Python generics
- **Context isolation** for unit-of-work boundaries
- **Built-in web server** for HTTP endpoints

## Architecture

Nether implements the **Actor Model** where:

- **Module** handles specific message types.
- **Message** passing is the only form of communication between modules.
- **Mediator** routes messages to appropriate modules.
- **Context** provide isolated environments for message processing.

## Quick Example

```python
from dataclasses import dataclass
from nether import Nether
from nether.message import Command, Event
from nether.modules import Module

@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessOrder(Command):
    order_id: str
    amount: float

@dataclass(frozen=True, slots=True, kw_only=True)
class OrderProcessed(Event):
    order_id: str

class OrderProcessor(Module[ProcessOrder]):
    async def handle(self, message, *, handler, channel):
        # Process the order
        print(f"Processing order {message.order_id} for ${message.amount}")
        
        # Send completion event
        await handler(OrderProcessed(order_id=message.order_id))

class System(Nether):
    async def main(self):
        self.attach(OrderProcessor(self))
        
        async with self.mediator.context() as ctx:
            await ctx.process(ProcessOrder(order_id="123", amount=99.99))
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`  
3. Explore examples: `python examples/simple.py`
4. Read the [Actor Model documentation](docs/actor-model-analysis.md)

## License

See [LICENSE](LICENSE) file.
