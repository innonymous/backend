from dataclasses import asdict
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl, Field

from innonymous.domains.messages.entities import MessageEntity
from innonymous.domains.messages.enums import (
    MessageFragmentMentionType,
    MessageFragmentTextStyle,
    MessageFragmentType,
    MessageType,
)
from innonymous.utils import FastPydanticBaseModel

__all__ = (
    "MessageSchema",
    "MessageCreateSchema",
    "MessagesSchema",
    "MessageTextBodySchema",
    "MessageFilesBodySchema",
    "MessageUpdateSchema",
    "MessageFragmentMentionUserSchema",
    "MessageFragmentMentionChatSchema",
    "MessageFragmentMentionMessageSchema",
    "MessageFragmentMentionSchema",
    "MessageFragmentTextSchema",
    "MessageFragmentLinkSchema",
    "MessageFragmentSchema",
    "MessageForwardSchema",
)


class MessageFragmentMentionUserSchema(FastPydanticBaseModel):
    user: UUID = Field()
    type: Literal[MessageFragmentMentionType.USER] = Field(default=MessageFragmentMentionType.USER)  # noqa: A003


class MessageFragmentMentionChatSchema(FastPydanticBaseModel):
    chat: UUID = Field()
    type: Literal[MessageFragmentMentionType.CHAT] = Field(default=MessageFragmentMentionType.CHAT)  # noqa: A003


class MessageFragmentMentionMessageSchema(FastPydanticBaseModel):
    chat: UUID = Field()
    message: UUID = Field()
    type: Literal[MessageFragmentMentionType.MESSAGE] = Field(default=MessageFragmentMentionType.MESSAGE)  # noqa: A003


class MessageFragmentMentionSchema(FastPydanticBaseModel):
    # fmt: off
    mention: MessageFragmentMentionUserSchema \
             | MessageFragmentMentionChatSchema \
             | MessageFragmentMentionMessageSchema = Field(discriminator="type")
    # fmt: on
    type: Literal[MessageFragmentType.MENTION] = Field(default=MessageFragmentType.MENTION)  # noqa: A003


class MessageFragmentTextSchema(FastPydanticBaseModel):
    text: str = Field()
    style: MessageFragmentTextStyle = Field(default=MessageFragmentTextStyle.NORMAL)
    type: Literal[MessageFragmentType.TEXT] = Field(default=MessageFragmentType.TEXT)  # noqa: A003


class MessageFragmentLinkSchema(FastPydanticBaseModel):
    link: AnyUrl = Field()
    text: str | None = Field(default=None)
    type: Literal[MessageFragmentType.LINK] = Field(default=MessageFragmentType.LINK)  # noqa: A003


MessageFragmentSchema = Annotated[
    MessageFragmentTextSchema | MessageFragmentLinkSchema | MessageFragmentMentionSchema,
    Field(discriminator="type"),
]


class MessageTextBodySchema(FastPydanticBaseModel):
    fragments: list[MessageFragmentSchema] = Field()
    type: Literal[MessageType.TEXT] = Field(default=MessageType.TEXT)  # noqa: A003


class MessageFilesBodySchema(FastPydanticBaseModel):
    files: list[UUID] = Field()
    fragments: list[MessageFragmentSchema] = Field(default=[])
    type: Literal[MessageType.FILES] = Field(default=MessageType.FILES)  # noqa: A003


class MessageForwardSchema(FastPydanticBaseModel):
    chat: UUID = Field()
    message: UUID = Field()


class MessageSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    chat: UUID = Field()
    author: UUID = Field()
    body: MessageTextBodySchema | MessageFilesBodySchema = Field(discriminator="type")

    replied_to: UUID | None = Field()
    forwarded_from: MessageForwardSchema | None = Field()
    updated_at: datetime = Field()
    created_at: datetime = Field()

    @classmethod
    def from_entity(cls, entity: MessageEntity) -> "MessageSchema":
        return cls.parse_obj(asdict(entity))


class MessageCreateSchema(FastPydanticBaseModel):
    replied_to: UUID | None = Field(default=None)
    forwarded_from: MessageForwardSchema | None = Field(default=None)
    body: str | MessageTextBodySchema | MessageFilesBodySchema | None = Field(default=None)
    files: list[UUID] | None = Field(default=None)


class MessageUpdateSchema(FastPydanticBaseModel):
    body: str | MessageTextBodySchema | MessageFilesBodySchema = Field()


class MessagesSchema(FastPydanticBaseModel):
    messages: list[MessageSchema] = Field()
