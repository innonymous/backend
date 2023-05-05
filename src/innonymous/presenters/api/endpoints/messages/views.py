from datetime import datetime
from uuid import UUID

from fastapi import Path, Query

from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.endpoints.messages import router
from innonymous.presenters.api.endpoints.messages.schemas import MessageSchema, MessagesSchema

__all__ = ("get", "filter")


@router.get("/messages/{id:uuid}", response_model=MessageSchema)
async def get(*, chat: UUID = Path(), id_: UUID = Path(alias="id")) -> MessageSchema:
    return MessageSchema.from_entity(await innonymous.get_message(chat, id_))


@router.get("/messages", response_model=MessagesSchema)
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
