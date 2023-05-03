from datetime import datetime
from typing import Any
from uuid import UUID

from innonymous.domains.messages.entities import MessageEntity
from innonymous.errors import InnonymousError

__all__ = (
    "MessagesError",
    "MessagesSerializingError",
    "MessagesDeserializingError",
    "MessagesNotFoundError",
    "MessagesTransactionError",
    "MessagesUpdateError",
)


class MessagesError(InnonymousError):
    pass


class MessagesSerializingError(MessagesError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: MessageEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> MessageEntity | None:
        return self._attributes["entity"]


class MessagesDeserializingError(MessagesError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: dict[str, Any] | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> dict[str, Any] | None:
        return self._attributes["entity"]


class MessagesNotFoundError(MessagesError):
    __message__ = "Message not found."

    def __init__(self, *, id_: UUID | None = None, chat: UUID | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["id"] = id_
        self._attributes["chat"] = chat

    @property
    def id(self) -> UUID | None:  # noqa: A003
        return self._attributes["id"]

    @property
    def chat(self) -> str | None:
        return self._attributes["chat"]


class MessagesTransactionError(MessagesNotFoundError):
    __message__ = "Cannot perform transaction. Entity does not exist or modified."

    def __init__(
        self,
        *,
        id_: UUID | None = None,
        chat: UUID | None = None,
        updated_at: datetime | None = None,
        message: str | None = None,
    ) -> None:
        super().__init__(id_=id_, chat=chat, message=message)
        self._attributes["updated_at"] = updated_at

    @property
    def updated_at(self) -> datetime | None:
        return self._attributes["updated_at"]


class MessagesUpdateError(MessagesError):
    __message__ = "Cannot update message."
