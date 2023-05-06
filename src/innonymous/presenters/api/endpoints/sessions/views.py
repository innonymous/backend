from uuid import UUID

from fastapi import Body, Depends, Header, HTTPException, Path, status

from innonymous.domains.sessions.entities import SessionEntity
from innonymous.domains.sessions.errors import SessionsNotFoundError
from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity
from innonymous.domains.users.errors import UsersNotFoundError
from innonymous.presenters.api.application import innonymous, tokens_interactor
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.domains.tokens.entities import TokenAccessEntity, TokenRefreshEntity
from innonymous.presenters.api.domains.tokens.errors import TokensInvalidError
from innonymous.presenters.api.endpoints.sessions import router
from innonymous.presenters.api.endpoints.sessions.schemas import (
    SessionSchema,
    SessionsSchema,
    TokenRefreshSchema,
    TokensSchema,
)
from innonymous.presenters.api.endpoints.users.schemas import UserCredentialsSchema

__all__ = ("get", "create", "delete", "delete_all")


@router.get("", response_model=SessionsSchema)
async def get(*, user: UserEntity = Depends(get_current_user)) -> SessionsSchema:
    sessions = []

    async for entity in innonymous.filter_sessions(user=user.id):
        sessions.append(SessionSchema.from_entity(entity))

    return SessionsSchema(sessions=sessions)


@router.post("", response_model=TokensSchema, status_code=status.HTTP_201_CREATED)
async def create(
    *, credentials: UserCredentialsSchema = Body(), user_agent: str = Header(default="", include_in_schema=False)
) -> TokensSchema:
    # Authenticate.
    user = await innonymous.get_user(credentials=UserCredentialsEntity(**credentials.dict()))

    # Create session.
    session = SessionEntity(user=user.id, agent=user_agent)
    await innonymous.create_session(session)

    return TokensSchema(
        access_token=tokens_interactor.encode(TokenAccessEntity(user=user.id, session=session.id)),
        refresh_token=tokens_interactor.encode(TokenRefreshEntity(user=user.id, session=session.id)),
    )


@router.patch("", response_model=TokensSchema)
async def update(*, body: TokenRefreshSchema = Body()) -> TokensSchema:
    try:
        token: TokenRefreshEntity = tokens_interactor.decode(
            body.refresh_token, audience="refresh"
        )  # type: ignore[assignment]

        # Update session.
        await innonymous.update_session(token.user, token.session)

    except TokensInvalidError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exception

    except SessionsNotFoundError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.") from exception

    except UsersNotFoundError as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.") from exception

    return TokensSchema(
        access_token=tokens_interactor.encode(TokenAccessEntity(user=token.user, session=token.session)),
        refresh_token=tokens_interactor.encode(TokenRefreshEntity(user=token.user, session=token.session)),
    )


@router.delete("/{id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(*, id_: UUID = Path(alias="id"), user: UserEntity = Depends(get_current_user)) -> None:
    await innonymous.delete_session(user.id, session=id_)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all(*, user: UserEntity = Depends(get_current_user)) -> None:
    await innonymous.delete_session(user.id)
