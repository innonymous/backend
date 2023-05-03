from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from pymongo import ASCENDING, IndexModel
from pymongo.collation import Collation

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import (
    UsersDeserializingError,
    UsersError,
    UsersNotFoundError,
    UsersSerializingError,
    UsersTransactionError,
)
from innonymous.utils import AsyncLazyObject

__all__ = ("UsersRepository",)


class UsersRepository(AsyncLazyObject):
    async def __ainit__(self, storage: MongoDBStorage, *, collection: str = "users") -> None:
        self.__storage = storage

        try:
            self.__collection = storage.client[collection]

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
                        (("updated", ASCENDING),),
                        name="users_updated_idx",
                        expireAfterSeconds=timedelta(days=30).total_seconds(),
                    ),
                ]
            )

        except Exception as exception:
            message = f"Cannot initialize database: {exception}"
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

    async def create(self, entity: UserEntity) -> None:
        serialized = self.__serialize(entity)

        try:
            await self.__collection.insert_one(serialized)

        # TODO: add exceptions for duplicated alias or id.
        except Exception as exception:
            message = f"Cannot perform creating: {exception}"
            raise UsersError(message) from exception

    async def update(self, entity: UserEntity, *, updated: datetime | None = None) -> None:
        serialized = self.__serialize(entity)
        query = self.__get_query(updated=updated)

        try:
            result = await self.__collection.update_one(query, {"$set": serialized})

        # TODO: add exceptions for duplicated alias or id.
        except Exception as exception:
            message = f"Cannot perform updating: {exception}"
            raise UsersError(message) from exception

        # Success.
        if result.modified_count > 0:
            return

        if updated is not None:
            raise UsersTransactionError(id_=entity.id, alias=entity.alias, updated=updated)

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
        *, id_: UUID | None = None, alias: str | None = None, updated: datetime | None = None
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}

        if id_ is not None:
            query["id"] = id_.hex

        if alias is not None:
            query["alias"] = alias

        if updated is not None:
            query["updated"] = updated

        return query

    @staticmethod
    def __serialize(entity: UserEntity) -> dict[str, Any]:
        try:
            serialized = asdict(entity)
            serialized["id"] = serialized["id"].hex
            serialized["updated"] = serialized["updated"]

            return serialized

        except Exception as exception:
            raise UsersSerializingError(entity) from exception

    @staticmethod
    def __deserialize(entity: dict[str, Any]) -> UserEntity:
        try:
            entity["updated"] = entity["updated"].replace(tzinfo=timezone.utc)
            return UserEntity(**entity)

        except Exception as exception:
            raise UsersDeserializingError(entity) from exception
