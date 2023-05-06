from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.application import innonymous, tokens_interactor
from innonymous.presenters.api.domains.tokens.entities import TokenAccessEntity
from innonymous.presenters.api.errors import APIUnauthorizedError

__all__ = ("get_current_user",)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> UserEntity:
    if credentials is None:
        raise APIUnauthorizedError()

    try:
        token: TokenAccessEntity = tokens_interactor.decode(
            credentials.credentials, audience="access"
        )  # type: ignore[assignment]

        # Retrieve session.
        session = await innonymous.get_session(token.session)

        # Validate nonce.
        if session.nonce != token.nonce:
            raise APIUnauthorizedError()

        return await innonymous.get_user(id_=token.user)

    except APIUnauthorizedError as exception:
        raise exception

    except Exception as exception:
        raise APIUnauthorizedError() from exception
