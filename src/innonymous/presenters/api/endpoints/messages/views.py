from datetime import datetime
from uuid import UUID

from fastapi import Body, Depends, Path, Query, status

from innonymous.domains.messages.entities import (
    MessageCreateEntity,
    MessageFilesBodyEntity,
    MessageTextBodyEntity,
    MessageUpdateEntity,
)
from innonymous.domains.users.entities import UserEntity
from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.dependencies import get_current_user
from innonymous.presenters.api.endpoints.messages import router
from innonymous.presenters.api.endpoints.messages.schemas import (
    MessageCreateSchema,
    MessageSchema,
    MessagesSchema,
    MessageUpdateSchema,
)
from innonymous.presenters.api.endpoints.schemas import ErrorSchema

__all__ = ("get", "filter", "create", "delete")


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
    search: str | None = Query(default=None),
    author: UUID | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    limit: int = Query(default=100, gt=0, le=250),
) -> MessagesSchema:
    messages = []
    async for entity in innonymous.filter_messages(
        chat, search=search, author=author, created_after=created_after, created_before=created_before, limit=limit
    ):
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
    kwargs = body.dict()

    # If user provides string or files.
    if isinstance(body.body, str) or (body.body is None and body.files is not None):
        fragments = await innonymous.string_to_fragments(body.body) if body.body is not None else []

        if body.files is not None:
            kwargs["body"] = MessageFilesBodyEntity(fragments=fragments, files=body.files)

        else:
            kwargs["body"] = MessageTextBodyEntity(fragments=fragments)

    return MessageSchema.from_entity(
        await innonymous.create_message(MessageCreateEntity(chat=chat, author=user.id, **kwargs))
    )


@router.patch(
    "/{id}",
    response_model=MessageSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def update(
    *,
    chat: UUID = Path(),
    id_: UUID = Path(alias="id"),
    body: MessageUpdateSchema = Body(),
    user: UserEntity = Depends(get_current_user),
) -> MessageSchema:
    return MessageSchema.from_entity(
        await innonymous.update_message(user.id, MessageUpdateEntity(id=id_, chat=chat, **body.dict()))
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorSchema},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorSchema},
    },
)
async def delete(
    *, chat: UUID = Path(), id_: UUID = Path(alias="id"), user: UserEntity = Depends(get_current_user)
) -> None:
    await innonymous.delete_message(user.id, chat, id_)
