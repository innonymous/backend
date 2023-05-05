from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field
from pydantic.dataclasses import dataclass

from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.events.enums import EventType
from innonymous.domains.messages.entities import MessageEntity
from innonymous.domains.users.entities import UserEntity

__all__ = (
    "EventEntity",
    "EventChatCreatedEntity",
    "EventUserCreatedEntity",
    "EventUserUpdatedEntity",
    "EventUserDeletedEntity",
    "EventMessageCreatedEntity",
    "EventMessageUpdatedEntity",
    "EventMessageDeletedEntity",
)


@dataclass
class EventChatCreatedEntity:
    chat: ChatEntity = Field()
    type: Literal[EventType.CHAT_CREATED] = Field(default=EventType.CHAT_CREATED)  # noqa: A003


@dataclass
class EventUserCreatedEntity:
    user: UserEntity = Field()
    type: Literal[EventType.USER_CREATED] = Field(default=EventType.USER_CREATED)  # noqa: A003


@dataclass
class EventUserUpdatedEntity:
    user: UserEntity = Field()
    type: Literal[EventType.USER_UPDATED] = Field(default=EventType.USER_UPDATED)  # noqa: A003


@dataclass
class EventUserDeletedEntity:
    user: UUID = Field()
    type: Literal[EventType.USER_DELETED] = Field(default=EventType.USER_DELETED)  # noqa: A003


@dataclass
class EventMessageCreatedEntity:
    message: MessageEntity = Field()
    type: Literal[EventType.MESSAGE_CREATED] = Field(default=EventType.MESSAGE_CREATED)  # noqa: A003


@dataclass
class EventMessageUpdatedEntity:
    message: MessageEntity = Field()
    type: Literal[EventType.MESSAGE_UPDATED] = Field(default=EventType.MESSAGE_UPDATED)  # noqa: A003


@dataclass
class EventMessageDeletedEntity:
    message: UUID = Field()
    type: Literal[EventType.MESSAGE_DELETED] = Field(default=EventType.MESSAGE_DELETED)  # noqa: A003


EventEntity = Annotated[
    EventChatCreatedEntity
    | EventUserCreatedEntity
    | EventUserUpdatedEntity
    | EventUserDeletedEntity
    | EventMessageCreatedEntity
    | EventMessageUpdatedEntity
    | EventMessageDeletedEntity,
    Field(discriminator="type"),
]
