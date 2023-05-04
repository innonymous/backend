from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.collation import Collation
from pymongo.errors import DuplicateKeyError

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.chats.errors import (
    ChatsAlreadyExistsError,
    ChatsDeserializingError,
    ChatsError,
    ChatsNotFoundError,
    ChatsSerializingError,
    ChatsTransactionError,
)
from innonymous.utils import AsyncLazyObject

__all__ = ("ChatsRepository",)


class ChatsRepository(AsyncLazyObject):
    async def __ainit__(
        self, storage: MongoDBStorage, *, collection: str = "chats", ttl: timedelta = timedelta(days=30)
    ) -> None:
        self.__storage = storage

        try:
            self.__collection = self.__storage.client[collection]

            await self.__collection.create_indexes(
                [
                    IndexModel((("id", ASCENDING),), name="chats_id_idx", unique=True),
                    IndexModel(
                        (("alias", ASCENDING),),
                        name="chats_alias_idx",
                        unique=True,
                        collation=Collation(locale="en_US", strength=1),
                    ),
                    IndexModel((("name", ASCENDING),), name="chats_name_idx"),
                    IndexModel(
                        (("updated_at", DESCENDING),),
                        name="chats_updated_at_idx",
                        unique=True,
                        expireAfterSeconds=ttl.total_seconds(),
                    ),
                ]
            )

        except Exception as exception:
            message = f"Cannot initialize collection: {exception}"
            raise ChatsError(message) from exception

    async def get(self, *, id_: UUID | None = None, alias: str | None = None) -> ChatEntity | None:
        # Avoid providing both id and alias or providing None.
        if (id_ is None) == (alias is None):
            message = "You should provide id or alias."
            raise ChatsError(message)

        query = self.__get_query(id_=id_, alias=alias)

        try:
            entity = await self.__collection.find_one(query)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise ChatsError(message) from exception

        if entity is None:
            return None

        return self.__deserialize(entity)

    async def filter(  # noqa: A003
        self, *, updated_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[ChatEntity]:
        query = self.__get_query(updated_before=updated_before)

        try:
            async for entity in self.__collection.find(
                query, sort=(("updated_at", DESCENDING),), limit=limit if limit is not None else 0
            ):
                yield self.__deserialize(entity)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise ChatsError(message) from exception

    async def create(self, entity: ChatEntity) -> None:
        serialized = self.__serialize(entity)

        try:
            await self.__collection.insert_one(serialized)

        except DuplicateKeyError as exception:
            raise ChatsAlreadyExistsError(id_=entity.id, alias=entity.alias) from exception

        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise ChatsError(message) from exception

    async def update(self, entity: ChatEntity, *, updated_at: datetime | None = None) -> None:
        serialized = self.__serialize(entity)
        query = self.__get_query(id_=entity.id, updated_at=updated_at)

        try:
            result = await self.__collection.update_one(query, {"$set": serialized})

        except DuplicateKeyError as exception:
            raise ChatsAlreadyExistsError(id_=entity.id, alias=entity.alias) from exception

        except Exception as exception:
            message = f"Cannot perform updating: {exception}"
            raise ChatsError(message) from exception

        # Success.
        if result.modified_count > 0:
            return

        if updated_at is not None:
            raise ChatsTransactionError(id_=entity.id, alias=entity.alias, updated_at=updated_at)

        raise ChatsNotFoundError(id_=entity.id, alias=entity.alias)

    async def shutdown(self) -> None:
        await self.__storage.shutdown()

    @staticmethod
    def __get_query(
        *,
        id_: UUID | None = None,
        alias: str | None = None,
        updated_at: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if alias is not None:
            query["alias"] = alias

        if updated_at is not None:
            query["updated_at"] = updated_at

        if updated_before is not None:
            query["updated_at"] = {"$lte": updated_before}

        return query

    @staticmethod
    def __serialize(entity: ChatEntity) -> dict[str, Any]:
        try:
            serialized = asdict(entity)
            serialized["id"] = serialized["id"].hex
            return serialized

        except Exception as exception:
            raise ChatsSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(entity: dict[str, Any]) -> ChatEntity:
        try:
            entity["updated_at"] = entity["updated_at"].replace(tzinfo=timezone.utc)
            return ChatEntity(**entity)

        except Exception as exception:
            raise ChatsDeserializingError(entity=entity) from exception
