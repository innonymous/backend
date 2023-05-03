from datetime import datetime
from typing import Any
from uuid import UUID

from innonymous.domains.users.entities import UserEntity
from innonymous.errors import InnonymousError

__all__ = (
    "UsersError",
    "UsersAlreadyExistsError",
    "UsersSerializingError",
    "UsersDeserializingError",
    "UsersNotFoundError",
    "UsersTransactionError",
    "UsersInvalidCredentialsError",
)


class UsersError(InnonymousError):
    pass


class UsersAlreadyExistsError(InnonymousError):
    __message__ = "User already exists."

    def __init__(self, *, id_: UUID | None = None, alias: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["id"] = id_
        self._attributes["alias"] = alias

    @property
    def id(self) -> UUID | None:  # noqa: A003
        return self._attributes["id"]

    @property
    def alias(self) -> str | None:
        return self._attributes["alias"]


class UsersSerializingError(InnonymousError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: UserEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> UserEntity | None:
        return self._attributes["entity"]


class UsersDeserializingError(InnonymousError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: dict[str, Any] | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> dict[str, Any] | None:
        return self._attributes["entity"]


class UsersNotFoundError(InnonymousError):
    __message__ = "User not found."

    def __init__(self, *, id_: UUID | None = None, alias: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["id"] = id_
        self._attributes["alias"] = alias

    @property
    def id(self) -> UUID | None:  # noqa: A003
        return self._attributes["id"]

    @property
    def alias(self) -> str | None:
        return self._attributes["alias"]


class UsersTransactionError(UsersNotFoundError):
    __message__ = "Cannot perform transaction. Entity does not exist or modified."

    def __init__(
        self,
        *,
        id_: UUID | None = None,
        alias: str | None = None,
        updated_at: datetime | None = None,
        message: str | None = None,
    ) -> None:
        super().__init__(id_=id_, alias=alias, message=message)
        self._attributes["updated_at"] = updated_at

    @property
    def updated_at(self) -> datetime | None:
        return self._attributes["updated_at"]


class UsersInvalidCredentialsError(InnonymousError):
    __message__ = "Credentials are invalid."
