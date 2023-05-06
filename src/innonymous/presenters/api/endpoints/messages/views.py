from datetime import datetime
from uuid import UUID

from fastapi import Body, Depends, Path, Query, status

from innonymous.domains.messages.entities import MessageEntity
from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.endpoints.messages import router
from innonymous.presenters.api.endpoints.messages.schemas import MessageCreateSchema, MessageSchema, MessagesSchema
from innonymous.presenters.api.endpoints.schemas import ErrorSchema

__all__ = ("get", "filter", "create")


@router.get(
    "/{id}",
    response_model=MessageSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def get(*, chat: UUID = Path(), id_: UUID = Path(alias="id")) -> MessageSchema:
    return MessageSchema.from_entity(await innonymous.get_message(chat, id_))


@router.get("", response_model=MessagesSchema, responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema}})
async def filter(  # noqa: A001
    *,
    chat: UUID = Path(),
    created_before: datetime | None = Query(default=None),
    limit: int | None = Query(default=None),
) -> MessagesSchema:
    messages = []
    async for entity in innonymous.filter_messages(chat, created_before=created_before, limit=limit):
        messages.append(MessageSchema.from_entity(entity))

    return MessagesSchema(messages=messages)


@router.post(
    "",
    response_model=MessageSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def create(
    *, chat: UUID = Path(), body: MessageCreateSchema = Body(), user: UserEntity = Depends(get_current_user)
) -> MessageSchema:
    message = MessageEntity(chat=chat, author=user.id, **body.dict())
    await innonymous.create_message(message)
    return MessageSchema.from_entity(message)
