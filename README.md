# Nether

> Nether means beneath, below, or underneath — representing both our minimalistic goals and system-level thinking.

## What is Nether?

Nether is a lightweight framework for rapid development and deployment of web services, built primarily on Python's standard library. Originally created to serve internal needs at Arjuna, it may or may not suit your use case — our goal is not to build a universal framework, but one that works best for us.

## Philosophy

- Favor the standard library – minimize external dependencies.
- Embrace asynchronous IO and efficient background task scheduling.
- Service failures shouldn't crash the app – services handle their own errors.
- Focus on observability and graceful shutdown (no orphaned threads).
- Avoid premature complexity – Clean Architecture & DDD come later.
<<<<<<< HEAD

## Features

- Asynchronous message bus and mediator pattern
- Modular service registration and isolation
- Simple event, command, and query handling
- Built-in support for background processing and graceful shutdown
- Minimal dependencies, easy to extend

## Architecture

Nether uses a mediator to route messages (commands, events, queries) between modules. Each module handles a specific concern and can be started or stopped independently. Contexts provide isolation for units of work.

## Quick Example

```python
from dataclasses import dataclass

from nether import Application
from nether.common import Command, Event
from nether.component import Component

@dataclass(frozen=True, slots=True, kw_only=True)
class MyCommand(Command):
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class MyEvent(Event):
    pass

class MyModule(Component[MyCommand]):
    async def handle(self, message, *, dispatch, join_stream):
        await dispatch(MyEvent())

class MyApp(Application):
    async def main(self):
        self.register_module(Component(self))
        async with self.mediator.context() as ctx:
            await ctx.process(MyCommand())

```

## Getting Started

- Clone the repo and install requirements (if any)
- See `examples/` for usage patterns
- Run `python examples/workflow_examples.py` for a workflow demo

## License

See LICENSE file.
=======
>>>>>>> 7bd618766ee643ba796831da0ab491b1d42ac94d
