from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from innonymous.domains.messages.entities import MessageFragmentEntity, validate_fragments


__all__ = ("UserEntity", "UserUpdateEntity", "UserCredentialsEntity")


@dataclass
class UserEntity:
    salt: bytes = Field()
    payload: bytes = Field()
    alias: str = Field(regex=r"^[a-zA-Z0-9]\w{3,30}[a-zA-Z0-9]$")

    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    favorites: list[UUID] = Field(default=[])
    name: str = Field(default="", regex=r"^.{0,64}$")
    about: list[MessageFragmentEntity] = Field(default=[])
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @validator("updated_at", always=True)
    def __validate_updated_at(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)

    @validator("about", always=True)
    def __validate_about(cls, fragments: list[MessageFragmentEntity]) -> list[MessageFragmentEntity]:
        return validate_fragments(fragments, max_length=256)


@dataclass
class UserUpdateEntity:
    id: UUID = Field()  # noqa: A003

    favorites: list[UUID] | None = Field(default=None)
    name: str | None = Field(default=None, regex=r"^.{0,64}$")
    alias: str | None = Field(default=None, regex=r"^[a-zA-Z0-9]\w{3,30}[a-zA-Z0-9]$")
    about: list[MessageFragmentEntity] | None = Field(default=None)
    password: str | None = Field(default=None, regex=r"^.{8,64}$")


@dataclass
class UserCredentialsEntity:
    alias: str = Field(regex=r"^[a-zA-Z0-9]\w{3,30}[a-zA-Z0-9]$")
    password: str = Field(regex=r"^.{8,64}$")
