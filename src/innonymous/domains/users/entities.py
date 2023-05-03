from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

__all__ = ("UserEntity", "UserUpdateEntity", "UserCredentialsEntity")


@dataclass
class UserEntity:
    alias: str = Field(regex=r"^\w{5,32}$")
    salt: bytes = Field()
    payload: bytes = Field()
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    id: UUID = Field(default_factory=uuid4)  # noqa: A003

    @validator("updated_at", always=True)
    def __validate_updated_at(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


@dataclass
class UserUpdateEntity:
    id: UUID = Field()  # noqa: A003
    alias: str | None = Field(default=None, regex=r"^\w{5,32}$")
    password: str | None = Field(default=None, regex=r"^.{8,64}$")


@dataclass
class UserCredentialsEntity:
    alias: str = Field(regex=r"^\w{5,32}$")
    password: str = Field(regex=r"^.{8,64}$")
