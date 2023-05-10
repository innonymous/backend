from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

__all__ = ("TokenEntity", "TokenAccessEntity", "TokenRefreshEntity", "TokenCaptchaEntity")


@dataclass
class TokenAccessEntity:
    user: UUID = Field()
    session: UUID = Field()
    nonce: int = Field()

    audience: Literal["access"] = Field(default="access")
    issued_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(hours=1))

    @validator("issued_at", "expires_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


@dataclass
class TokenRefreshEntity:
    user: UUID = Field()
    session: UUID = Field()
    nonce: int = Field()

    audience: Literal["refresh"] = Field(default="refresh")
    issued_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(days=30))

    @validator("issued_at", "expires_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


@dataclass
class TokenCaptchaEntity:
    hash: bytes = Field()  # noqa: A003

    audience: Literal["captcha"] = Field(default="captcha")
    issued_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(minutes=1))

    @validator("issued_at", "expires_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


TokenEntity = Annotated[TokenAccessEntity | TokenRefreshEntity | TokenCaptchaEntity, Field(discriminator="audience")]
