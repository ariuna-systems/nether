from abc import abstractmethod
from typing import Protocol


class Runnable(Protocol):
    @abstractmethod
    def run() -> None: ...


class Stoppable(Protocol):
    @abstractmethod
    def stop() -> None: ...
