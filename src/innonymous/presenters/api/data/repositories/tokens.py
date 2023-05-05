from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from jwt import PyJWT
from pydantic import parse_obj_as

from innonymous.presenters.api.domains.tokens.entities import (
    TokenAccessEntity,
    TokenCaptchaEntity,
    TokenEntity,
    TokenRefreshEntity,
)
from innonymous.presenters.api.domains.tokens.errors import (
    TokensDeserializingError,
    TokensError,
    TokensInvalidError,
    TokensSerializingError,
)

__all__ = ("TokensRepository",)


class TokensRepository:
    ALGORITHM = "HS256"

    def __init__(self, key: str) -> None:
        self.__jwt = PyJWT()
        self.__key = key

    def get(self, token: str, *, audience: str | None = None) -> TokenEntity:
        try:
            decoded = self.__jwt.decode(token, self.__key, [self.ALGORITHM], audience=audience)

        except Exception as exception:
            raise TokensInvalidError(token=token) from exception

        return self.__deserialize(decoded)

    def create(self, entity: TokenEntity) -> str:
        serialized = self.__serialize(entity)

        try:
            return self.__jwt.encode(serialized, self.__key, self.ALGORITHM)

        except Exception as exception:
            message = f"Cannot create token: {exception}"
            raise TokensError(message) from exception

    @staticmethod
    def __serialize(entity: TokenEntity) -> dict[str, Any]:
        try:
            serialized: dict[str, Any] = {
                "aud": entity.audience,
                "iat": int(entity.issued_at.timestamp()),
                "exp": int(entity.expires_at.timestamp()),
            }

            if isinstance(entity, TokenCaptchaEntity):
                serialized["hash"] = entity.hash.hex()

            elif isinstance(entity, TokenAccessEntity | TokenRefreshEntity):
                serialized["user"] = entity.user.hex
                serialized["session"] = entity.session.hex

            return serialized

        except Exception as exception:
            raise TokensSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(entity: dict[str, Any]) -> TokenEntity:
        try:
            deserialized = {
                "audience": entity["aud"],
                "issued_at": datetime.fromtimestamp(entity["iat"], tz=timezone.utc),
                "expires_at": datetime.fromtimestamp(entity["exp"], tz=timezone.utc),
            }

            if entity["aud"] == "captcha":
                deserialized["hash"] = bytes.fromhex(entity["hash"])

            if entity["aud"] in ("access", "refresh"):
                deserialized["user"] = UUID(entity["user"])
                deserialized["session"] = UUID(entity["session"])

            return parse_obj_as(TokenEntity, deserialized)  # type: ignore[arg-type]

        except Exception as exception:
            raise TokensDeserializingError(entity=entity) from exception
