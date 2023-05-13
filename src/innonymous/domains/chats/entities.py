from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

__all__ = ("ChatEntity",)


@dataclass
class ChatEntity:
    alias: str = Field(regex=r"^[a-zA-Z0-9]\w{3,30}[a-zA-Z0-9]$")

    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    name: str = Field(default="", regex=r"^.{0,64}$")
    about: str = Field(default="", regex=r"^(.|\n){0,128}$")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @validator("updated_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)
