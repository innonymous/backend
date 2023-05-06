import re
from datetime import datetime
from uuid import UUID

from fastapi import Path, Query
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from starlette import status

from innonymous.domains.chats.entities import ChatEntity
from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.endpoints.chats import router
from innonymous.presenters.api.endpoints.chats.schemas import ChatSchema, ChatsSchema
from innonymous.presenters.api.endpoints.schemas import ErrorSchema

__all__ = ("get", "filter")


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


@router.get("", response_model=ChatsSchema)
async def filter(  # noqa: A001
    *, updated_before: datetime | None = Query(default=None), limit: int | None = Query(default=None)
) -> ChatsSchema:
    chats = []
    async for entity in innonymous.filter_chats(updated_before=updated_before, limit=limit):
        chats.append(ChatSchema.from_entity(entity))

    return ChatsSchema(chats=chats)
