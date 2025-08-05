from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True, slots=True)
class Message:
  created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
  created_by: str | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class Command(Message): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class Query(Message): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class Event(Message): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class SuccessEvent(Event): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class FailureEvent(Event):
  error: Exception


@dataclass(frozen=True, kw_only=True, slots=True)
class StopProducer(Command):
  """Message to signal producer to stop producing events."""
