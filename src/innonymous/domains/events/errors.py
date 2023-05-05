from innonymous.domains.events.entities import EventEntity
from innonymous.errors import InnonymousError

__all__ = ("EventsError", "EventsSerializingError", "EventsDeserializingError")


class EventsError(InnonymousError):
    pass


class EventsSerializingError(EventsError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: EventEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> EventEntity | None:
        return self._attributes["entity"]


class EventsDeserializingError(EventsError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: bytes | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> bytes | None:
        return self._attributes["entity"]
