from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from pydantic import Field

from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.endpoints.captcha.schemas import CaptchaSolvedSchema
from innonymous.utils import FastPydanticBaseModel

__all__ = ("UserSchema", "UserCredentialsSchema", "UserCreateSchema")


class UserSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    name: str = Field()
    alias: str = Field()
    about: str = Field()
    updated_at: datetime = Field()
    favorites: list[UUID] = Field()

    @classmethod
    def from_entity(cls, entity: UserEntity) -> "UserSchema":
        return cls.parse_obj(asdict(entity))


class UserCredentialsSchema(FastPydanticBaseModel):
    alias: str = Field()
    password: str = Field()


class UserCreateSchema(FastPydanticBaseModel):
    captcha: CaptchaSolvedSchema = Field()
    credentials: UserCredentialsSchema = Field()
