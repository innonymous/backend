import re
from uuid import UUID

from fastapi import Body, Depends, Path, status
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper

from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity, UserUpdateEntity
from innonymous.presenters.api.application import captcha_interactor, innonymous
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.domains.captcha.entities import CaptchaSolvedEntity
from innonymous.presenters.api.endpoints.schemas import ErrorSchema
from innonymous.presenters.api.endpoints.users import router
from innonymous.presenters.api.endpoints.users.schemas import (
    UserCreateSchema,
    UserPrivateSchema,
    UserSchema,
    UserUpdateSchema,
)

__all__ = ("get", "get_me", "create", "update", "delete")


@router.get(
    "/me",
    response_model=UserPrivateSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def get_me(*, user: UserEntity = Depends(get_current_user)) -> UserPrivateSchema:
    return UserPrivateSchema.from_entity(await innonymous.get_user(id_=user.id))


@router.get(
    "/{id}",
    response_model=UserSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def get(*, id_: str = Path(alias="id")) -> UserSchema:
    if re.match(UserEntity.alias.regex, id_) is not None:  # type: ignore[attr-defined]
        return UserSchema.from_entity(await innonymous.get_user(alias=id_))

    try:
        uuid = UUID(id_)

    except Exception as exception:
        raise ValidationError([ErrorWrapper(ValueError("Invalid alias or id."), "id")], UserSchema) from exception

    return UserSchema.from_entity(await innonymous.get_user(id_=uuid))


@router.post(
    "",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def create(*, body: UserCreateSchema = Body()) -> UserSchema:
    # Check that captcha is valid.
    captcha_interactor.verify(CaptchaSolvedEntity(**body.captcha.dict()))
    # Create user.
    return UserSchema.from_entity(await innonymous.create_user(UserCredentialsEntity(**body.credentials.dict())))


@router.patch(
    "/me",
    response_model=UserPrivateSchema,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def update(*, body: UserUpdateSchema = Body(), user: UserEntity = Depends(get_current_user)) -> UserPrivateSchema:
    entity = body.dict()

    if body.password is not None:
        # Validate old password.
        await innonymous.get_user(credentials=UserCredentialsEntity(alias=user.alias, password=body.password.old))
        # Allow password change.
        entity["password"] = body.password.new

    return UserPrivateSchema.from_entity(await innonymous.update_user(UserUpdateEntity(id=user.id, **entity)))


@router.delete(
    "/me", status_code=status.HTTP_204_NO_CONTENT, responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema}}
)
async def delete(*, user: UserEntity = Depends(get_current_user)) -> None:
    await innonymous.delete_user(user.id)
