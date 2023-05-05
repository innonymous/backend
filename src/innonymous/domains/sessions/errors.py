from datetime import datetime
from typing import Any
from uuid import UUID

from innonymous.domains.sessions.entities import SessionEntity
from innonymous.errors import InnonymousError

__all__ = (
    "SessionsError",
    "SessionsSerializingError",
    "SessionsDeserializingError",
    "SessionsNotFoundError",
    "SessionsTransactionError",
)


class SessionsError(InnonymousError):
    pass


class SessionsSerializingError(SessionsError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: SessionEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> SessionEntity | None:
        return self._attributes["entity"]


class SessionsDeserializingError(SessionsError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: dict[str, Any] | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> dict[str, Any] | None:
        return self._attributes["entity"]


class SessionsNotFoundError(SessionsError):
    __message__ = "Session not found."

    def __init__(self, *, id_: UUID | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["id"] = id_

    @property
    def id(self) -> UUID | None:  # noqa: A003
        return self._attributes["id"]


class SessionsTransactionError(SessionsNotFoundError):
    __message__ = "Cannot perform transaction. Entity does not exist or modified."

    def __init__(
        self,
        *,
        id_: UUID | None = None,
        updated_at: datetime | None = None,
        message: str | None = None,
    ) -> None:
        super().__init__(id_=id_, message=message)
        self._attributes["updated_at"] = updated_at

    @property
    def updated_at(self) -> datetime | None:
        return self._attributes["updated_at"]
