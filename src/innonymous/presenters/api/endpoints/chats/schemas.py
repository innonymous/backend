from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from pydantic import Field

from innonymous.domains.chats.entities import ChatEntity
from innonymous.presenters.api.endpoints.captcha.schemas import CaptchaSolvedSchema
from innonymous.utils import FastPydanticBaseModel

__all__ = ("ChatSchema", "ChatCreateSchema", "ChatsSchema", "ChatInfoSchema")


class ChatSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    name: str = Field()
    alias: str = Field()
    about: str = Field()
    updated_at: datetime = Field()

    @classmethod
    def from_entity(cls, entity: ChatEntity) -> "ChatSchema":
        return cls.parse_obj(asdict(entity))


class ChatInfoSchema(FastPydanticBaseModel):
    alias: str = Field()
    name: str = Field(default="")
    about: str = Field(default="")


class ChatCreateSchema(FastPydanticBaseModel):
    info: ChatInfoSchema = Field()
    captcha: CaptchaSolvedSchema = Field()


class ChatsSchema(FastPydanticBaseModel):
    chats: list[ChatSchema] = Field()
