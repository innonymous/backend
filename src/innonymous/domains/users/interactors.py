import dataclasses
import os
from asyncio import get_running_loop
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity, UserUpdateEntity
from innonymous.domains.users.errors import UsersError, UsersInvalidCredentialsError, UsersNotFoundError

__all__ = ("UsersInteractor",)


class UsersInteractor:
    # Scrypt options.
    # https://stackoverflow.com/questions/11126315/what-are-optimal-scrypt-work-factors/30308723#30308723
    SALT_LENGTH = 16
    PAYLOAD_LENGTH = 32
    ITERATIONS = 2**14
    BLOCK_SIZE = 8
    PARALLELIZATION = 1

    def __init__(self, repository: UsersRepository) -> None:
        self.__repository = repository

    async def get(
        self, *, id_: UUID | None = None, alias: str | None = None, credentials: UserCredentialsEntity | None = None
    ) -> UserEntity:
        if credentials is not None:
            alias = credentials.alias

        entity = await self.__repository.get(id_=id_, alias=alias)

        if entity is None:
            raise UsersNotFoundError(id_=id_, alias=alias)

        if credentials is not None:
            await self.__verify_scrypt(entity.salt, credentials.password, entity.payload)

        return entity

    def filter(  # noqa: A003
        self,
        *,
        search: str | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[UserEntity]:
        return self.__repository.filter(
            search=search, updated_after=updated_after, updated_before=updated_before, limit=limit
        )

    async def create(self, entity: UserCredentialsEntity) -> UserEntity:
        # Credentials.
        salt = os.urandom(self.SALT_LENGTH)
        payload = await self.__derive_scrypt(salt, entity.password)

        # Create user in database.
        user_entity = UserEntity(alias=entity.alias, salt=salt, payload=payload)
        await self.__repository.create(user_entity)

        return user_entity

    async def update(self, entity: UserUpdateEntity) -> UserEntity:
        kwargs: dict[str, Any] = {"updated_at": datetime.now(tz=timezone.utc)}

        if entity.favorites is not None:
            kwargs["favorites"] = entity.favorites

        if entity.name is not None:
            kwargs["name"] = entity.name

        if entity.alias is not None:
            kwargs["alias"] = entity.alias

        if entity.about is not None:
            kwargs["about"] = entity.about

        if entity.password is not None:
            kwargs["salt"] = os.urandom(self.SALT_LENGTH)
            kwargs["payload"] = await self.__derive_scrypt(kwargs["salt"], entity.password)

        # Update using transaction.
        old_user_entity = await self.get(id_=entity.id)
        new_user_entity = dataclasses.replace(old_user_entity, **kwargs)
        await self.__repository.update(new_user_entity, updated_at=old_user_entity.updated_at)

        return new_user_entity

    async def delete(self, id_: UUID) -> None:
        if not await self.__repository.delete(id_):
            raise UsersNotFoundError(id_=id_)

    async def shutdown(self) -> None:
        await self.__repository.shutdown()

    @classmethod
    async def __derive_scrypt(cls, salt: bytes, password: str) -> bytes:
        try:
            # Run in thread to avoid any blocking.
            return await get_running_loop().run_in_executor(None, cls.__get_scrypt(salt).derive, password.encode())

        except Exception as exception:
            message = "Cannot derive scrypt."
            raise UsersError(message) from exception

    @classmethod
    async def __verify_scrypt(cls, salt: bytes, password: str, expected: bytes) -> None:
        try:
            # Run in thread to avoid any blocking.
            return await get_running_loop().run_in_executor(
                None, cls.__get_scrypt(salt).verify, password.encode(), expected
            )

        except Exception as exception:
            raise UsersInvalidCredentialsError() from exception

    @classmethod
    def __get_scrypt(cls, salt: bytes) -> Scrypt:
        try:
            return Scrypt(salt, cls.PAYLOAD_LENGTH, cls.ITERATIONS, cls.BLOCK_SIZE, cls.PARALLELIZATION)

        except Exception as exception:
            message = "Cannot create scrypt."
            raise UsersError(message) from exception
