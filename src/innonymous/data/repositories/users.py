from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.collation import Collation
from pymongo.errors import DuplicateKeyError

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import (
    UsersAlreadyExistsError,
    UsersDeserializingError,
    UsersError,
    UsersNotFoundError,
    UsersSerializingError,
    UsersTransactionError,
)
from innonymous.utils import AsyncLazyObject

__all__ = ("UsersRepository",)


class UsersRepository(AsyncLazyObject):
    async def __ainit__(
        self, storage: MongoDBStorage, *, collection: str = "users", ttl: timedelta = timedelta(days=30)
    ) -> None:
        self.__storage = storage

        try:
            self.__collection = self.__storage.client[collection]

            await self.__collection.create_indexes(
                [
                    IndexModel((("id", ASCENDING),), name="users_id_idx", unique=True),
                    IndexModel(
                        (("alias", ASCENDING),),
                        name="users_alias_idx",
                        unique=True,
                        collation=Collation(locale="en_US", strength=1),
                    ),
                    IndexModel(
                        (("updated_at", ASCENDING),),
                        name="users_updated_at_idx",
                        expireAfterSeconds=ttl.total_seconds(),
                    ),
                    IndexModel((("name", TEXT), ("alias", TEXT), ("about", TEXT)), name="chats_search_idx"),
                ]
            )

        except Exception as exception:
            message = f"Cannot initialize collection: {exception}"
            raise UsersError(message) from exception

    async def get(self, *, id_: UUID | None = None, alias: str | None = None) -> UserEntity | None:
        # Avoid providing both id and alias or providing None.
        if (id_ is None) == (alias is None):
            message = "You should provide id or alias."
            raise UsersError(message)

        query = self.__get_query(id_=id_, alias=alias)

        try:
            entity = await self.__collection.find_one(query)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise UsersError(message) from exception

        if entity is None:
            return None

        return self.__deserialize(entity)

    async def filter(  # noqa: A003
        self,
        *,
        search: str | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[UserEntity]:
        query = self.__get_query(search=search, updated_after=updated_after, updated_before=updated_before)

        # Most resent first.
        sort: list[tuple[str, Any]] = []

        # Score on search score.
        if search is not None:
            sort.append(("textScore", {"$meta": "textScore"}))

        # Only updated_after.
        if updated_after is not None and updated_before is None:
            sort.append(("updated_at", ASCENDING))

        # Only updated_before.
        if updated_before is not None and updated_after is None:
            sort.append(("updated_at", DESCENDING))

        try:
            async for entity in self.__collection.find(
                query,
                sort=sort,
                limit=limit if limit is not None else 0,
                projection={"textScore": {"$meta": "textScore"}} if search is not None else None,
            ):
                yield self.__deserialize(entity)

        except Exception as exception:
            message = f"Cannot perform query: {exception}"
            raise UsersError(message) from exception

    async def create(self, entity: UserEntity) -> None:
        serialized = self.__serialize(entity)

        try:
            await self.__collection.insert_one(serialized)

        except DuplicateKeyError as exception:
            raise UsersAlreadyExistsError(id_=entity.id, alias=entity.alias) from exception

        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise UsersError(message) from exception

    async def update(self, entity: UserEntity, *, updated_at: datetime | None = None) -> None:
        serialized = self.__serialize(entity)
        query = self.__get_query(id_=entity.id, updated_at=updated_at)

        try:
            result = await self.__collection.update_one(query, {"$set": serialized})

        except DuplicateKeyError as exception:
            raise UsersAlreadyExistsError(id_=entity.id, alias=entity.alias) from exception

        except Exception as exception:
            message = f"Cannot perform updating: {exception}"
            raise UsersError(message) from exception

        # Success.
        if result.matched_count > 0:
            return

        if updated_at is not None:
            raise UsersTransactionError(id_=entity.id, alias=entity.alias, updated_at=updated_at)

        raise UsersNotFoundError(id_=entity.id, alias=entity.alias)

    async def delete(self, id_: UUID) -> bool:
        query = self.__get_query(id_=id_)

        try:
            result = await self.__collection.delete_one(query)

        except Exception as exception:
            message = f"Cannot perform deleting: {exception}"
            raise UsersError(message) from exception

        return result.deleted_count > 0

    async def shutdown(self) -> None:
        await self.__storage.shutdown()

    @staticmethod
    def __get_query(
        *,
        id_: UUID | None = None,
        alias: str | None = None,
        search: str | None = None,
        updated_at: datetime | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if alias is not None:
            query["alias"] = alias

        if updated_at is not None:
            query["updated_at"] = updated_at

        updated_at_range = {}

        if updated_after is not None:
            updated_at_range["$gte"] = updated_after

        if updated_before is not None:
            updated_at_range["$lte"] = updated_before

        if updated_at_range != {}:
            query["updated_at"] = updated_at_range

        if search is not None:
            query["$text"] = {"$search": search}

        return query

    @staticmethod
    def __serialize(entity: UserEntity) -> dict[str, Any]:
        try:
            serialized = asdict(entity)
            serialized["id"] = serialized["id"].hex
            serialized["favorites"] = [id_.hex for id_ in entity.favorites]
            return serialized

        except Exception as exception:
            raise UsersSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(entity: dict[str, Any]) -> UserEntity:
        try:
            entity["updated_at"] = entity["updated_at"].replace(tzinfo=timezone.utc)
            return UserEntity(**entity)

        except Exception as exception:
            raise UsersDeserializingError(entity=entity) from exception
