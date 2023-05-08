import re
from datetime import datetime
from uuid import UUID

from fastapi import Body, Depends, Path, Query, status
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper

from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.application import captcha_interactor, innonymous
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.domains.captcha.entities import CaptchaSolvedEntity
from innonymous.presenters.api.endpoints.chats import router
from innonymous.presenters.api.endpoints.chats.schemas import ChatCreateSchema, ChatSchema, ChatsSchema
from innonymous.presenters.api.endpoints.schemas import ErrorSchema

__all__ = ("get", "filter", "create")


@router.get(
    "/{id}",
    response_model=ChatSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def get(*, id_: str = Path(alias="id")) -> ChatSchema:
    if re.match(ChatEntity.alias.regex, id_) is not None:  # type: ignore[attr-defined]
        return ChatSchema.from_entity(await innonymous.get_chat(alias=id_))

    try:
        uuid = UUID(id_)

    except Exception as exception:
        raise ValidationError([ErrorWrapper(ValueError("Invalid alias or id."), "id")], ChatSchema) from exception

    return ChatSchema.from_entity(await innonymous.get_chat(id_=uuid))


@router.get("", response_model=ChatsSchema, responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema}})
async def filter(  # noqa: A001
    *,
    search: str | None = Query(default=None),
    updated_after: datetime | None = Query(default=None),
    updated_before: datetime | None = Query(default=None),
    limit: int = Query(default=100, gt=0, le=250),
) -> ChatsSchema:
    chats = []
    async for entity in innonymous.filter_chats(
        search=search, updated_after=updated_after, updated_before=updated_before, limit=limit
    ):
        chats.append(ChatSchema.from_entity(entity))

    return ChatsSchema(chats=chats)


@router.post(
    "",
    response_model=ChatSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def create(*, body: ChatCreateSchema = Body(), user: UserEntity = Depends(get_current_user)) -> ChatSchema:
    captcha_interactor.verify(CaptchaSolvedEntity(**body.captcha.dict()))

    # Create chat.
    chat = ChatEntity(**body.info.dict())
    await innonymous.create_chat(user.id, chat)
    return ChatSchema.from_entity(chat)
