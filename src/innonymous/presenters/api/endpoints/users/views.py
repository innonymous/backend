import re
from uuid import UUID

from fastapi import Body, Depends, HTTPException, Path, status

from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity
from innonymous.presenters.api.application import captcha_interactor, innonymous
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.domains.captcha.entities import CaptchaSolvedEntity
from innonymous.presenters.api.endpoints.users import router
from innonymous.presenters.api.endpoints.users.schemas import UserCreateSchema, UserSchema

__all__ = ("create",)


@router.get("/{id:str}", response_model=UserSchema)
async def get(*, id_: str = Path(alias="id")) -> UserSchema:
    if re.match(r"^\w{5,32}$", id_) is not None:
        return UserSchema.from_entity(await innonymous.get_user(alias=id_))

    try:
        uuid = UUID(id_)

    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid alias or id.") from exception

    return UserSchema.from_entity(await innonymous.get_user(id_=uuid))


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create(*, body: UserCreateSchema = Body()) -> UserSchema:
    # Check that captcha is valid.
    captcha_interactor.verify(CaptchaSolvedEntity(**body.captcha.dict()))
    # Create user.
    return UserSchema.from_entity(await innonymous.create_user(UserCredentialsEntity(**body.credentials.dict())))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(*, user: UserEntity = Depends(get_current_user)) -> None:
    await innonymous.delete_user(user.id)
