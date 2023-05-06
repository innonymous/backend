from dataclasses import asdict
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from innonymous.domains.messages.entities import MessageEntity
from innonymous.domains.messages.enums import MessageType
from innonymous.utils import FastPydanticBaseModel

__all__ = ("MessageSchema", "MessageCreateSchema", "MessagesSchema", "MessageTextBodySchema", "MessageFilesBodySchema")


class MessageTextBodySchema(FastPydanticBaseModel):
    data: str = Field()
    type: Literal[MessageType.TEXT] = Field(default=MessageType.TEXT)  # noqa: A003


class MessageFilesBodySchema(FastPydanticBaseModel):
    data: list[UUID] = Field()
    description: str | None = Field(default=None)
    type: Literal[MessageType.FILES] = Field(default=MessageType.FILES)  # noqa: A003


class MessageSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    chat: UUID = Field()
    author: UUID = Field()
    body: MessageTextBodySchema | MessageFilesBodySchema = Field(discriminator="type")

    replied_to: UUID | None = Field()
    forwarded_from: UUID | None = Field()
    updated_at: datetime = Field()
    created_at: datetime = Field()

    @classmethod
    def from_entity(cls, entity: MessageEntity) -> "MessageSchema":
        return cls.parse_obj(asdict(entity))


class MessageCreateSchema(FastPydanticBaseModel):
    body: MessageTextBodySchema | MessageFilesBodySchema = Field(discriminator="type")
    replied_to: UUID | None = Field(default=None)
    forwarded_from: UUID | None = Field(default=None)


class MessagesSchema(FastPydanticBaseModel):
    messages: list[MessageSchema] = Field()
