import asyncio
from asyncio import Event
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Any, AsyncIterator
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.errors import InvalidOperation

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.messages.entities import (
    MessageEntity,
    MessageFilesBodyEntity,
    MessageFragmentLinkEntity,
    MessageFragmentTextEntity,
)
from innonymous.domains.messages.enums import MessageFragmentType
from innonymous.domains.messages.errors import (
    MessagesDeserializingError,
    MessagesError,
    MessagesNotFoundError,
    MessagesSerializingError,
    MessagesTransactionError,
)
from innonymous.utils import AsyncLazyObject

__all__ = ("MessagesRepository",)


class MessagesRepository(AsyncLazyObject):
    async def __ainit__(
        self,
        storage: MongoDBStorage,
        *,
        collections_prefix: str = "chat",
        ttl: timedelta = timedelta(days=30),
        clear_period: timedelta = timedelta(minutes=5),
    ) -> None:
        self.__storage = storage
        self.__collections_prefix = collections_prefix
        self.__ttl = ttl.total_seconds()

        self.__is_stopped = Event()
        self.__worker = asyncio.create_task(self.__clear_empty_collections_worker(period=clear_period))

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
        self,
        chat: UUID,
        *,
        search: str | None = None,
        author: UUID | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[MessageEntity]:
        query = self.__get_query(
            search=search, author=author, created_after=created_after, created_before=created_before
        )
        collection = await self.__get_collection(chat)

        # Most resent first.
        sort: list[tuple[str, Any]] = []

        # Score on search score.
        if search is not None:
            sort.append(("textScore", {"$meta": "textScore"}))

        # Only created_after.
        if created_after is not None and created_before is None:
            sort.append(("created_at", ASCENDING))

        # Only created_before.
        if created_before is not None and created_after is None:
            sort.append(("created_at", DESCENDING))

        try:
            async for entity in collection.find(
                query,
                sort=sort,
                limit=limit if limit is not None else 0,
                projection={"textScore": {"$meta": "textScore"}} if search is not None else None,
            ):
                yield self.__deserialize(chat, entity)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
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
        if result.matched_count > 0:
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
        self.__is_stopped.set()
        await self.__worker

    @staticmethod
    def __get_query(
        *,
        id_: UUID | None = None,
        search: str | None = None,
        author: UUID | None = None,
        updated_at: datetime | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if updated_at is not None:
            query["updated_at"] = updated_at

        if author is not None:
            query["author"] = author.hex

        created_at_range = {}

        if created_after is not None:
            created_at_range["$gte"] = created_after

        if created_before is not None:
            created_at_range["$lte"] = created_before

        if created_at_range != {}:
            query["created_at"] = created_at_range

        if search is not None:
            query["$text"] = {"$search": search}

        return query

    @staticmethod
    def __serialize(entity: MessageEntity) -> dict[str, Any]:  # noqa: PLR0912
        try:
            serialized = asdict(entity)

            # We do not need to store it, since we store id in collection name.
            serialized.pop("chat")

            # Serialise UUIDs in root entity.
            for field, value in serialized.items():
                if isinstance(value, UUID):
                    serialized[field] = value.hex

            # Serialise UUIDs in fragments.
            for fragment in serialized["body"]["fragments"]:
                if fragment["type"] != MessageFragmentType.MENTION:
                    continue

                # Mention fragment contains object "mention" with UUIDs.
                for field, value in fragment["mention"].items():
                    if isinstance(value, UUID):
                        fragment["mention"][field] = value.hex

            # Serialise UUIDs in files body entity.
            if isinstance(entity.body, MessageFilesBodyEntity):
                serialized["body"]["files"] = [id_.hex for id_ in entity.body.files]

            # Serialise UUIDs in forwarded entity.
            if entity.forwarded_from is not None:
                serialized["forwarded_from"]["chat"] = entity.forwarded_from.chat.hex
                serialized["forwarded_from"]["message"] = entity.forwarded_from.message.hex

            search = []
            for fragment in entity.body.fragments:
                if isinstance(fragment, MessageFragmentTextEntity):
                    search.append(fragment.text)

                elif isinstance(fragment, MessageFragmentLinkEntity):
                    search.append(fragment.link)

                    if fragment.text is not None:
                        search.append(fragment.text)

            # This field will be used for searching.
            serialized["_search"] = " ".join(search)

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
                    IndexModel((("_search", TEXT),), name="messages_search_idx"),
                ]
            )

            return collection

        except Exception as exception:
            message = f"Cannot initialize collection: {exception}"
            raise MessagesError(message) from exception

    async def __clear_empty_collections_worker(self, *, period: timedelta = timedelta(minutes=5)) -> None:
        last_clearing = datetime.now(tz=timezone.utc)

        while not self.__is_stopped.is_set():
            if datetime.now(tz=timezone.utc) - last_clearing < period:
                await asyncio.sleep(1)
                continue

            try:
                last_clearing = datetime.now(tz=timezone.utc)

                for collection in await self.__storage.client.list_collections(
                    filter={"name": {"$regex": f"^{self.__collections_prefix}_[a-f0-9]{{32}}$"}}
                ):
                    if await self.__storage.client[collection["name"]].estimated_document_count() == 0:
                        await self.__storage.client.drop_collection(collection["name"])

            except InvalidOperation:
                break

            except Exception as exception:
                getLogger().exception(f"Cannot delete empty collections: {exception}")
