from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from innonymous.domains.sessions.errors import SessionsNotFoundError
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import UsersNotFoundError
from innonymous.presenters.api.application import innonymous, tokens_interactor
from innonymous.presenters.api.domains.tokens.errors import TokensInvalidError

__all__ = ("get_current_user",)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> UserEntity:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Provide authentication token.")

    try:
        token = tokens_interactor.get(credentials.credentials, audience="access")

        # Validate session.
        await innonymous.get_session(token.session)

        return await innonymous.get_user(id_=token.user)

    except TokensInvalidError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exception

    except SessionsNotFoundError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.") from exception

    except UsersNotFoundError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.") from exception
