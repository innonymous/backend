from datetime import datetime
from typing import Any
from uuid import UUID

from innonymous.domains.chats.entities import ChatEntity
from innonymous.errors import InnonymousError

__all__ = (
    "ChatsError",
    "ChatsAlreadyExistsError",
    "ChatsSerializingError",
    "ChatsDeserializingError",
    "ChatsNotFoundError",
    "ChatsTransactionError",
)


class ChatsError(InnonymousError):
    pass


class ChatsAlreadyExistsError(ChatsError):
    __message__ = "Chat already exists."

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


class ChatsSerializingError(ChatsError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: ChatEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> ChatEntity | None:
        return self._attributes["entity"]


class ChatsDeserializingError(ChatsError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: dict[str, Any] | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> dict[str, Any] | None:
        return self._attributes["entity"]


class ChatsNotFoundError(ChatsError):
    __message__ = "Chat not found."

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


class ChatsTransactionError(ChatsNotFoundError):
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
