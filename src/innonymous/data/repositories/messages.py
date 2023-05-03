from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, IndexModel

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.messages.entities import MessageEntity, MessageFilesBodyEntity
from innonymous.domains.messages.errors import (
    MessagesDeserializingError,
    MessagesError,
    MessagesNotFoundError,
    MessagesSerializingError,
    MessagesTransactionError,
)

__all__ = ("MessagesRepository",)


class MessagesRepository:
    def __init__(
        self, storage: MongoDBStorage, *, collections_prefix: str = "chat", ttl: timedelta = timedelta(days=30)
    ) -> None:
        self.__storage = storage
        self.__collections_prefix = collections_prefix
        self.__ttl = ttl.total_seconds()

    async def get(self, chat: UUID, id_: UUID) -> MessageEntity | None:
        query = self.__get_query(id_=id_)
        collection = await self.__get_collection(chat)

        try:
            entity = await collection.find_one(query)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise MessagesError(message) from exception

        if entity is None:
            return None

        return self.__deserialize(chat, entity)

    async def filter(  # noqa: A003
        self, chat: UUID, *, created_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[MessageEntity]:
        query = self.__get_query(created_before=created_before)
        collection = await self.__get_collection(chat)

        try:
            async for entity in collection.find(
                query, sort=(("created_at", DESCENDING),), limit=limit if limit is not None else 0
            ):
                yield self.__deserialize(chat, entity)

        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise MessagesError(message) from exception

    async def create(self, entity: MessageEntity) -> None:
        serialized = self.__serialize(entity)
        collection = await self.__get_collection(entity.chat)

        try:
            await collection.insert_one(serialized)

        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise MessagesError(message) from exception

    async def update(self, entity: MessageEntity, *, updated_at: datetime | None = None) -> None:
        serialized = self.__serialize(entity)
        collection = await self.__get_collection(entity.chat)
        query = self.__get_query(id_=entity.id, updated_at=updated_at)

        try:
            result = await collection.update_one(query, {"$set": serialized})

        except Exception as exception:
            message = f"Cannot perform updating: {exception}"
            raise MessagesError(message) from exception

        # Success.
        if result.modified_count > 0:
            return

        if updated_at is not None:
            raise MessagesTransactionError(id_=entity.id, chat=entity.chat, updated_at=updated_at)

        raise MessagesNotFoundError(id_=entity.id, chat=entity.chat)

    async def delete(self, chat: UUID, id_: UUID) -> bool:
        query = self.__get_query(id_=id_)
        collection = await self.__get_collection(chat)

        try:
            result = await collection.delete_one(query)

        except MessagesError as exception:
            raise exception

        except Exception as exception:
            message = f"Cannot perform deleting: {exception}"
            raise MessagesError(message) from exception

        return result.deleted_count > 0

    async def shutdown(self) -> None:
        await self.__storage.shutdown()

    @staticmethod
    def __get_query(
        *, id_: UUID | None = None, updated_at: datetime | None = None, created_before: datetime | None = None
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if updated_at is not None:
            query["updated_at"] = updated_at

        if created_before is not None:
            query["created_at"] = {"$lte": created_before}

        return query

    @staticmethod
    def __serialize(entity: MessageEntity) -> dict[str, Any]:
        try:
            serialized = asdict(entity)

            # We do not need to store it, since we store id in collection name.
            serialized.pop("chat")

            serialized["id"] = serialized["id"].hex
            serialized["author"] = serialized["author"].hex

            if isinstance(entity.body, MessageFilesBodyEntity):
                serialized["body"]["data"] = [id_.hex for id_ in serialized["body"]["data"]]

            return serialized

        except Exception as exception:
            raise MessagesSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(chat: UUID, entity: dict[str, Any]) -> MessageEntity:
        try:
            entity["updated_at"] = entity["updated_at"].replace(tzinfo=timezone.utc)
            entity["created_at"] = entity["created_at"].replace(tzinfo=timezone.utc)
            return MessageEntity(**entity, chat=chat)

        except Exception as exception:
            raise MessagesDeserializingError(entity=entity) from exception

    async def __get_collection(self, chat: UUID) -> AsyncIOMotorCollection:
        try:
            collection = self.__storage.client[f"{self.__collections_prefix}_{chat.hex}"]

            await collection.create_indexes(
                [
                    IndexModel((("id", ASCENDING),), name="messages_id_idx", unique=True),
                    IndexModel(
                        (("created_at", DESCENDING),),
                        name="messages_created_at_idx",
                        unique=True,
                        expireAfterSeconds=self.__ttl,
                    ),
                    IndexModel((("updated_at", ASCENDING),), name="messages_updated_at_idx"),
                ]
            )

            return collection

        except Exception as exception:
            message = f"Cannot initialize collection: {exception}"
            raise MessagesError(message) from exception
