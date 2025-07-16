# Nether

*Nether means located beneath or below, lower or under.*

**Nether je framework pro rychlé vytváření a nasazení asynchronních aplikací a webových služeb.**

Tento framework vznikl z interních potřeb <https://arjuna.group>, může ale nemusí vyhovovat tvým potřebám.
Našim cílem není vytvořit projekt, který bude vyhovovat všem, ale především nám!
Základem je využít naplno standardní knihovnu a používat minimum externích balíčků.

## Charakteristiky

- **Type-safe**: Využívá Python 3.12+ generics a protocols pro type safety
- **Message-oriented**: Komunikace přes typed messages (Command, Query, Event)
- **Mediator pattern**: Centralizované směrování zpráv přes mediator
- **Async-first**: Postaveno na asyncio pro neblokující operace
- **Service isolation**: Selhání jedné služby neovlivní ostatní
- **Context management**: Izolované zpracování požadavků přes MediatorContext

## Požadavky

- Python 3.12+
- aiohttp (pro HTTP server)
- aiohttp-middlewares (CORS podpora)
- python-dotenv (konfigurace)

## Základní použití

```python
import argparse
from nether import Application, run_main
from nether.service import Service
from nether.server import HTTPInterfaceService

class MyApplication(Application):
    async def main(self) -> None:
        # Registrace HTTP serveru
        http_service = HTTPInterfaceService()
        self.register_service(http_service)
        
        # Spuštění serveru
        async with self.mediator.context() as ctx:
            await ctx.process(StartServer(host="localhost", port=8080))

if __name__ == "__main__":
    config = argparse.Namespace()
    app = MyApplication(configuration=config)
    run_main(app.start())
```

## Architektura

### Klíčové komponenty

- **Application**: Hlavní třída aplikace s lifecycle managementem
- **Service**: Bazová třída pro služby s typed message handling
- **Mediator**: Centrální dispatcher pro zprávy mezi službami
- **MediatorContext**: Izolované prostředí pro zpracování unit of work
- **Messages**: Typed zprávy (Command, Query, Event) pro komunikaci

### Message Types

```python
from dataclasses import dataclass
from nether.common import Command, Query, Event

@dataclass(frozen=True)
class CreateUser(Command):
    name: str
    email: str

@dataclass(frozen=True)
class GetUser(Query):
    user_id: int

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: int
    name: str
```

### Service Implementation

```python
from nether.service import Service
from nether.common import Message

class UserService(Service[CreateUser | GetUser]):
    async def handle(self, message: Message, *, dispatch, join_stream) -> None:
        match message:
            case CreateUser(name=name, email=email):
                # Zpracování vytvoření uživatele
                user_id = await self.create_user(name, email)
                await dispatch(UserCreated(user_id=user_id, name=name))
            case GetUser(user_id=user_id):
                # Zpracování dotazu na uživatele
                user = await self.get_user(user_id)
                await dispatch(UserFound(user=user))
```

## Implementované funkce

### ✅ Hotovo

- **Core Framework**: Application, Service, Mediator
- **Type Safety**: Generics a protocols pro compile-time checking
- **HTTP Server**: HTTPInterfaceService s aiohttp
- **Message System**: Command/Query/Event pattern
- **Context Management**: Izolované zpracování požadavků
- **Service Lifecycle**: Start/stop management s graceful shutdown
- **Error Handling**: Izolace chyb mezi službami
- **Signal Handling**: Graceful shutdown na SIGINT/SIGTERM

### 🔄 Extensions

- **nether-access**: Autentizace a autorizace (v extensions/)

### 📋 Roadmap

- **WebSocket podpora**: Real-time komunikace
- **Background Jobs**: Scheduled a interval-based úlohy  
- **Database integrace**: ORM/Query builder
- **Metrics & Monitoring**: Performance a health monitoring
- **Configuration Management**: Centralizované nastavení
- **Plugin System**: Dynamické načítání extensions

## Struktura projektu

```text
nether/
├── src/nether/           # Core framework
│   ├── application.py    # Application base class
│   ├── service.py        # Service base a protocols
│   ├── mediator.py       # Message mediator
│   ├── server.py         # HTTP server service
│   ├── common.py         # Message types
│   └── exceptions.py     # Error handling
├── extensions/           # Framework extensions
│   └── nether-access/    # Auth/authz extension
└── examples/             # Example applications
    └── server-simple.py  # Basic HTTP server
```

## Filozofie

Nether je postaven na těchto principech:

1. **Type Safety First**: Využívá moderní Python typing pro minimalizaci runtime chyb
2. **Message-Oriented**: Loosely coupled komunikace přes typed messages
3. **Isolation**: Služby jsou izolované a jejich selhání neovlivní ostatní
4. **Async Native**: Celý framework je postaven na asyncio
5. **Minimal Dependencies**: Používá jen nezbytné externí knihovny
6. **Czech-First**: Dokumentace a komentáře v češtině pro český tým
