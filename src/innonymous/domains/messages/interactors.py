import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from innonymous.data.repositories.messages import MessagesRepository
from innonymous.domains.messages.entities import (
    MessageCreateEntity,
    MessageEntity,
    MessageUpdateEntity,
)
from innonymous.domains.messages.errors import MessagesNotFoundError, MessagesUpdateError

__all__ = ("MessagesInteractor",)


class MessagesInteractor:
    def __init__(self, repository: MessagesRepository) -> None:
        self.__repository = repository

    async def get(self, chat: UUID, id_: UUID) -> MessageEntity:
        entity = await self.__repository.get(chat, id_)

        if entity is None:
            raise MessagesNotFoundError(id_=id_, chat=chat)

        return entity

    def filter(  # noqa: A003
        self, chat: UUID, *, created_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[MessageEntity]:
        return self.__repository.filter(chat, created_before=created_before, limit=limit)

    async def create(self, entity: MessageCreateEntity) -> MessageEntity:
        if entity.replied_to is not None:
            # Validate that message exists.
            await self.get(entity.chat, entity.replied_to)

        kwargs = dataclasses.asdict(entity)

        # Set body from forwarded message.
        if entity.forwarded_from is not None:
            original_message = await self.get(entity.forwarded_from.chat, entity.forwarded_from.message)
            kwargs["body"] = original_message.body

        # Create message.
        message_entity = MessageEntity(**kwargs)
        await self.__repository.create(message_entity)
        return message_entity

    async def update(self, entity: MessageUpdateEntity) -> MessageEntity:
        old_message_entity = await self.get(entity.chat, entity.id)
        kwargs: dict[str, Any] = {"updated_at": datetime.now(tz=timezone.utc)}

        if old_message_entity.forwarded_from is not None:
            message = "You cannot update forwarded message"
            raise MessagesUpdateError(message)

        if kwargs["updated_at"] - old_message_entity.created_at > timedelta(hours=1):
            message = "You cannot update message after one hour."
            raise MessagesUpdateError(message)

        if entity.body is not None:
            if old_message_entity.body.type != entity.body.type:
                message = "You cannot change message type."
                raise MessagesUpdateError(message)

            kwargs["body"] = entity.body

        # Update using transaction.
        new_message_entity = dataclasses.replace(old_message_entity, **kwargs)
        await self.__repository.update(new_message_entity, updated_at=old_message_entity.updated_at)

        return new_message_entity

    async def delete(self, chat: UUID, id_: UUID) -> None:
        if not await self.__repository.delete(chat, id_):
            raise MessagesNotFoundError(id_=id_, chat=chat)

    async def shutdown(self) -> None:
        await self.__repository.shutdown()
