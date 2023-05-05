import dataclasses
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

from innonymous.data.repositories.chats import ChatsRepository
from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.chats.errors import ChatsNotFoundError

__all__ = ("ChatsInteractor",)


class ChatsInteractor:
    def __init__(self, repository: ChatsRepository) -> None:
        self.__repository = repository

    async def get(self, *, id_: UUID | None = None, alias: str | None = None) -> ChatEntity:
        entity = await self.__repository.get(id_=id_, alias=alias)

        if entity is None:
            raise ChatsNotFoundError(id_=id_, alias=alias)

        return entity

    def filter(  # noqa: A003
        self, *, updated_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[ChatEntity]:
        return self.__repository.filter(updated_before=updated_before, limit=limit)

    async def create(self, entity: ChatEntity) -> None:
        return await self.__repository.create(entity)

    async def update(self, id_: UUID) -> None:
        old_entity = await self.get(id_=id_)
        new_entity = dataclasses.replace(old_entity, updated_at=datetime.now(tz=timezone.utc))
        await self.__repository.update(new_entity, updated_at=old_entity.updated_at)

    async def shutdown(self) -> None:
        await self.__repository.shutdown()
