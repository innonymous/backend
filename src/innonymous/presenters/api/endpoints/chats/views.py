import re
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, Path, Query, status

from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.endpoints.chats import router
from innonymous.presenters.api.endpoints.chats.schemas import ChatSchema, ChatsSchema

__all__ = ("get", "filter")


@router.get("/{id}", response_model=ChatSchema)
async def get(*, id_: str = Path(alias="id")) -> ChatSchema:
    if re.match(r"^\w{5,32}$", id_) is not None:
        return ChatSchema.from_entity(await innonymous.get_chat(alias=id_))

    try:
        uuid = UUID(id_)

    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid alias or id.") from exception

    return ChatSchema.from_entity(await innonymous.get_chat(id_=uuid))


@router.get("", response_model=ChatsSchema)
async def filter(  # noqa: A001
    *, updated_before: datetime | None = Query(default=None), limit: int | None = Query(default=None)
) -> ChatsSchema:
    chats = []
    async for entity in innonymous.filter_chats(updated_before=updated_before, limit=limit):
        chats.append(ChatSchema.from_entity(entity))

    return ChatsSchema(chats=chats)
