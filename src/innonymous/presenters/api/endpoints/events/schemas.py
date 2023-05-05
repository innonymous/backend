from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from innonymous.domains.events.enums import EventType
from innonymous.presenters.api.endpoints.chats.schemas import ChatSchema
from innonymous.presenters.api.endpoints.messages.schemas import MessageSchema
from innonymous.presenters.api.endpoints.users.schemas import UserSchema
from innonymous.utils import FastPydanticBaseModel

__all__ = (
    "EventSchema",
    "EventChatCreatedSchema",
    "EventUserCreatedSchema",
    "EventUserUpdatedSchema",
    "EventUserDeletedSchema",
    "EventMessageCreatedSchema",
    "EventMessageUpdatedSchema",
    "EventMessageDeletedSchema",
)


class EventChatCreatedSchema(FastPydanticBaseModel):
    chat: ChatSchema = Field()
    type: Literal[EventType.CHAT_CREATED] = Field(default=EventType.CHAT_CREATED)  # noqa: A003


class EventUserCreatedSchema(FastPydanticBaseModel):
    user: UserSchema = Field()
    type: Literal[EventType.USER_CREATED] = Field(default=EventType.USER_CREATED)  # noqa: A003


class EventUserUpdatedSchema(FastPydanticBaseModel):
    user: UserSchema = Field()
    type: Literal[EventType.USER_UPDATED] = Field(default=EventType.USER_UPDATED)  # noqa: A003


class EventUserDeletedSchema(FastPydanticBaseModel):
    user: UUID = Field()
    type: Literal[EventType.USER_DELETED] = Field(default=EventType.USER_DELETED)  # noqa: A003


class EventMessageCreatedSchema(FastPydanticBaseModel):
    message: MessageSchema = Field()
    type: Literal[EventType.MESSAGE_CREATED] = Field(default=EventType.MESSAGE_CREATED)  # noqa: A003


class EventMessageUpdatedSchema(FastPydanticBaseModel):
    message: MessageSchema = Field()
    type: Literal[EventType.MESSAGE_UPDATED] = Field(default=EventType.MESSAGE_UPDATED)  # noqa: A003


class EventMessageDeletedSchema(FastPydanticBaseModel):
    message: UUID = Field()
    type: Literal[EventType.MESSAGE_DELETED] = Field(default=EventType.MESSAGE_DELETED)  # noqa: A003


EventSchema = Annotated[
    EventChatCreatedSchema
    | EventUserCreatedSchema
    | EventUserUpdatedSchema
    | EventUserDeletedSchema
    | EventMessageCreatedSchema
    | EventMessageUpdatedSchema
    | EventMessageDeletedSchema,
    Field(discriminator="type"),
]
