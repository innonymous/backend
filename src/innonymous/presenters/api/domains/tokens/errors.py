from typing import Any

from innonymous.presenters.api.domains.tokens.entities import TokenEntity
from innonymous.presenters.api.errors import APIError

__all__ = ("TokensError", "TokensInvalidError", "TokensSerializingError", "TokensDeserializingError")


class TokensError(APIError):
    pass


class TokensInvalidError(TokensError):
    __message__ = "Token is invalid."

    def __init__(self, *, token: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["token"] = token

    @property
    def token(self) -> str | None:
        return self._attributes["token"]


class TokensSerializingError(TokensError):
    __message__ = "Cannot serialize entity."

    def __init__(self, *, entity: TokenEntity | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> TokenEntity | None:
        return self._attributes["entity"]


class TokensDeserializingError(TokensError):
    __message__ = "Cannot deserialize entity."

    def __init__(self, *, entity: dict[str, Any] | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["entity"] = entity

    @property
    def entity(self) -> dict[str, Any] | None:
        return self._attributes["entity"]
