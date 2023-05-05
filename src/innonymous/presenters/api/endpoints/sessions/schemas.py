from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from pydantic import Field

from innonymous.domains.sessions.entities import SessionEntity
from innonymous.utils import FastPydanticBaseModel

__all__ = ("SessionSchema", "SessionsSchema", "TokensSchema", "TokenRefreshSchema")


class SessionSchema(FastPydanticBaseModel):
    id: UUID = Field()  # noqa: A003
    agent: str = Field()
    updated_at: datetime = Field()

    @classmethod
    def from_entity(cls, entity: SessionEntity) -> "SessionSchema":
        return cls.parse_obj(asdict(entity))


class SessionsSchema(FastPydanticBaseModel):
    sessions: list[SessionSchema] = Field()


class TokensSchema(FastPydanticBaseModel):
    access_token: str = Field()
    refresh_token: str = Field()


class TokenRefreshSchema(FastPydanticBaseModel):
    refresh_token: str = Field()
