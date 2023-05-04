from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from innonymous.domains.messages.enums import MessageType

__all__ = ("MessageTextBodyEntity", "MessageFilesBodyEntity", "MessageEntity")


@dataclass
class MessageTextBodyEntity:
    data: str = Field(min_length=1, max_length=1024)
    type: Literal[MessageType.TEXT] = Field(default=MessageType.TEXT)  # noqa: A003


@dataclass
class MessageFilesBodyEntity:
    data: list[UUID] = Field(min_items=1, max_items=10)
    description: str | None = Field(default=None, min_length=1, max_length=1024)
    type: Literal[MessageType.FILES] = Field(default=MessageType.FILES)  # noqa: A003


@dataclass
class MessageEntity:
    chat: UUID = Field()
    author: UUID = Field()
    body: MessageTextBodyEntity | MessageFilesBodyEntity = Field(discriminator="type")
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    replied_to: UUID | None = Field(default=None)
    forwarded_from: UUID | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @validator("updated_at", "created_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


@dataclass
class MessageUpdateEntity:
    id: UUID = Field()  # noqa: A003
    chat: UUID = Field()
    body: MessageTextBodyEntity | MessageFilesBodyEntity | None = Field(default=None, discriminator="type")
