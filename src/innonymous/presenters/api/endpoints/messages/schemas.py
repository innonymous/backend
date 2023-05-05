from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from pydantic import Field

from innonymous.domains.messages.entities import MessageEntity, MessageFilesBodyEntity, MessageTextBodyEntity
from innonymous.utils import FastPydanticBaseModel

__all__ = ("MessageSchema", "MessagesSchema")


class MessageSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    chat: UUID = Field()
    author: UUID = Field()
    body: MessageTextBodyEntity | MessageFilesBodyEntity = Field(discriminator="type")

    replied_to: UUID | None = Field()
    forwarded_from: UUID | None = Field()
    updated_at: datetime = Field()
    created_at: datetime = Field()

    @classmethod
    def from_entity(cls, entity: MessageEntity) -> "MessageSchema":
        return cls.parse_obj(asdict(entity))


class MessagesSchema(FastPydanticBaseModel):
    messages: list[MessageSchema] = Field()
