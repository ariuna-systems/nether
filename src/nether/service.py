from typing import Self
import uuid
from nether.application import Application
from nether.common import Runnable


class Service(Runnable):
    def __init__(
        self,
        id: uuid.UUID,
        description: str = None,
        application: Application = None,
    ) -> None:
        self.id = id
        self.name = type(self).__name__
        self.application = application
        self.description = description

    @classmethod
    async def create(cls, id, name, description) -> Self:
        cls(id, name, description)

    def __eq__(self, other: Self) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
