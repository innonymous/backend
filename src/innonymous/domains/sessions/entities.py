from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

__all__ = ("SessionEntity",)


@dataclass
class SessionEntity:
    user: UUID = Field()
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    agent: str = Field(default="")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @validator("updated_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)
