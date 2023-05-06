from dataclasses import asdict
from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import Field

from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.endpoints.captcha.schemas import CaptchaSolvedSchema
from innonymous.utils import FastPydanticBaseModel

__all__ = (
    "UserSchema",
    "UserPrivateSchema",
    "UserCredentialsSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserPasswordUpdateSchema",
)

T = TypeVar("T", bound="UserSchema")


class UserSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    name: str = Field()
    alias: str = Field()
    about: str = Field()
    updated_at: datetime = Field()

    @classmethod
    def from_entity(cls: type[T], entity: UserEntity) -> T:
        return cls.parse_obj(asdict(entity))


class UserPrivateSchema(UserSchema):
    favorites: list[UUID] = Field()


class UserCredentialsSchema(FastPydanticBaseModel):
    alias: str = Field()
    password: str = Field()


class UserCreateSchema(FastPydanticBaseModel):
    captcha: CaptchaSolvedSchema = Field()
    credentials: UserCredentialsSchema = Field()


class UserPasswordUpdateSchema(FastPydanticBaseModel):
    old: str = Field()
    new: str = Field()


class UserUpdateSchema(FastPydanticBaseModel):
    name: str | None = Field(default=None)
    alias: str | None = Field(default=None)
    about: str | None = Field(default=None)
    favorites: list[UUID] | None = Field(default=None)
    password: UserPasswordUpdateSchema | None = Field(default=None)
