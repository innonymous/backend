from typing import AsyncContextManager, AsyncIterator

from innonymous.data.repositories.events import EventsRepository
from innonymous.domains.events.entities import EventEntity

__all__ = ("EventsInteractor",)


class EventsInteractor:
    def __init__(self, repository: EventsRepository) -> None:
        self.__repository = repository

    async def publish(self, entity: EventEntity) -> None:
        await self.__repository.publish(entity)

    def subscribe(self) -> AsyncContextManager[AsyncIterator[EventEntity]]:
        return self.__repository.subscribe()

    async def shutdown(self) -> None:
        await self.__repository.shutdown()
