from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from pymongo import ASCENDING, IndexModel

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.sessions.entities import SessionEntity
from innonymous.domains.sessions.errors import (
    SessionsDeserializingError,
    SessionsError,
    SessionsNotFoundError,
    SessionsSerializingError,
    SessionsTransactionError,
)
from innonymous.utils import AsyncLazyObject

__all__ = ("SessionsRepository",)


class SessionsRepository(AsyncLazyObject):
    async def __ainit__(
        self, storage: MongoDBStorage, *, collection: str = "sessions", ttl: timedelta = timedelta(days=30)
    ) -> None:
        self.__storage = storage

        try:
            self.__collection = self.__storage.client[collection]

            await self.__collection.create_indexes(
                [
                    IndexModel((("id", ASCENDING),), name="sessions_id_idx", unique=True),
                    IndexModel((("user", ASCENDING),), name="sessions_user_idx"),
                    IndexModel(
                        (("updated_at", ASCENDING),),
                        name="sessions_updated_at_idx",
                        unique=True,
                        expireAfterSeconds=ttl.total_seconds(),
                    ),
                ]
            )

        except Exception as exception:
            message = f"Cannot initialize collection: {exception}"
            raise SessionsError(message) from exception

    async def get(self, id_: UUID) -> SessionEntity | None:
        query = self.__get_query(id_=id_)

        try:
            entity = await self.__collection.find_one(query)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise SessionsError(message) from exception

        if entity is None:
            return None

        return self.__deserialize(entity)

    async def filter(self, *, user: UUID | None = None) -> AsyncIterator[SessionEntity]:  # noqa: A003
        query = self.__get_query(user=user)

        try:
            async for entity in self.__collection.find(query):
                yield self.__deserialize(entity)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise SessionsError(message) from exception

    async def create(self, entity: SessionEntity) -> None:
        serialized = self.__serialize(entity)

        try:
            await self.__collection.insert_one(serialized)

        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise SessionsError(message) from exception

    async def update(self, entity: SessionEntity, *, updated_at: datetime | None = None) -> None:
        serialized = self.__serialize(entity)
        query = self.__get_query(id_=entity.id, updated_at=updated_at)

        try:
            result = await self.__collection.update_one(query, {"$set": serialized})

        except Exception as exception:
            message = f"Cannot perform updating: {exception}"
            raise SessionsError(message) from exception

        # Success.
        if result.matched_count > 0:
            return

        if updated_at is not None:
            raise SessionsTransactionError(id_=entity.id, updated_at=updated_at)

        raise SessionsNotFoundError(id_=entity.id)

    async def delete(self, *, id_: UUID | None = None, user: UUID | None = None) -> int:
        # Avoid providing both id and alias or providing None.
        if (id_ is None) == (user is None):
            message = "You should provide id or user."
            raise SessionsError(message)

        query = self.__get_query(id_=id_, user=user)

        try:
            result = await self.__collection.delete_many(query)

        except Exception as exception:
            message = f"Cannot perform deleting: {exception}"
            raise SessionsError(message) from exception

        return result.deleted_count

    async def shutdown(self) -> None:
        await self.__storage.shutdown()

    @staticmethod
    def __get_query(
        *, id_: UUID | None = None, user: UUID | None = None, updated_at: datetime | None = None
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if user is not None:
            query["user"] = user.hex

        if updated_at is not None:
            query["updated_at"] = updated_at

        return query

    @staticmethod
    def __serialize(entity: SessionEntity) -> dict[str, Any]:
        try:
            serialized = asdict(entity)
            serialized["id"] = serialized["id"].hex
            serialized["user"] = serialized["user"].hex
            return serialized

        except Exception as exception:
            raise SessionsSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(entity: dict[str, Any]) -> SessionEntity:
        try:
            entity["updated_at"] = entity["updated_at"].replace(tzinfo=timezone.utc)
            return SessionEntity(**entity)

        except Exception as exception:
            raise SessionsDeserializingError(entity=entity) from exception
