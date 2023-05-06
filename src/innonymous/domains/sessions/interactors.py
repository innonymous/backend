import dataclasses
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

from innonymous.data.repositories.sessions import SessionsRepository
from innonymous.domains.sessions.entities import SessionEntity
from innonymous.domains.sessions.errors import SessionsNotFoundError

__all__ = ("SessionsInteractor",)


class SessionsInteractor:
    def __init__(self, repository: SessionsRepository) -> None:
        self.__repository = repository

    async def get(self, id_: UUID) -> SessionEntity:
        entity = await self.__repository.get(id_)

        if entity is None:
            raise SessionsNotFoundError(id_=id_)

        return entity

    def filter(self, *, user: UUID | None = None) -> AsyncIterator[SessionEntity]:  # noqa: A003
        return self.__repository.filter(user=user)

    async def create(self, entity: SessionEntity) -> None:
        return await self.__repository.create(entity)

    async def update(self, id_: UUID) -> SessionEntity:
        old_entity = await self.get(id_=id_)
        new_entity = dataclasses.replace(
            old_entity, updated_at=datetime.now(tz=timezone.utc), nonce=old_entity.nonce + 1
        )
        await self.__repository.update(new_entity, updated_at=old_entity.updated_at)
        return new_entity

    async def delete(self, *, id_: UUID | None = None, user: UUID | None = None) -> None:
        if await self.__repository.delete(id_=id_, user=user) == 0 and id_ is not None:
            raise SessionsNotFoundError(id_=id_)

    async def shutdown(self) -> None:
        await self.__repository.shutdown()
