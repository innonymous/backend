from datetime import datetime
from logging import getLogger
from typing import AsyncContextManager, AsyncIterator
from uuid import UUID

from innonymous.data.repositories.chats import ChatsRepository
from innonymous.data.repositories.events import EventsRepository
from innonymous.data.repositories.messages import MessagesRepository
from innonymous.data.repositories.users import UsersRepository
from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.data.storages.rabbitmq import RabbitMQStorage
from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.chats.interactors import ChatsInteractor
from innonymous.domains.events.entities import (
    EventChatCreatedEntity,
    EventEntity,
    EventMessageCreatedEntity,
    EventMessageDeletedEntity,
    EventMessageUpdatedEntity,
    EventUserCreatedEntity,
    EventUserDeletedEntity,
    EventUserUpdatedEntity,
)
from innonymous.domains.events.interactors import EventsInteractor
from innonymous.domains.messages.entities import MessageEntity, MessageUpdateEntity
from innonymous.domains.messages.errors import MessagesUpdateError
from innonymous.domains.messages.interactors import MessagesInteractor
from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity, UserUpdateEntity
from innonymous.domains.users.interactors import UsersInteractor
from innonymous.settings import Settings
from innonymous.utils import AsyncLazyObject

__all__ = ("Innonymous",)


class Innonymous(AsyncLazyObject):
    async def __ainit__(self) -> None:
        settings = Settings()
        main_mongodb_storage = await MongoDBStorage(settings.DATABASE_URL, db=settings.MAIN_DATABASE_NAME)

        self.__users_interactor = UsersInteractor(
            await UsersRepository(
                main_mongodb_storage, collection=settings.USERS_COLLECTION_NAME, ttl=settings.USERS_TTL
            )
        )
        self.__chats_interactor = ChatsInteractor(
            await ChatsRepository(
                main_mongodb_storage, collection=settings.CHATS_COLLECTION_NAME, ttl=settings.CHATS_TTL
            )
        )
        self.__events_interactor = EventsInteractor(
            EventsRepository(await RabbitMQStorage(settings.BROKER_URL, exchange=settings.BROKER_EXCHANGE))
        )
        self.__messages_interactor = MessagesInteractor(
            await MessagesRepository(
                await MongoDBStorage(settings.DATABASE_URL, db=settings.MESSAGES_DATABASE_NAME),
                collections_prefix=settings.MESSAGES_COLLECTION_PREFIX,
                ttl=settings.MESSAGES_TTL,
            ),
        )

    async def get_chat(self, *, id_: UUID | None = None, alias: str | None = None) -> ChatEntity:
        return await self.__chats_interactor.get(id_=id_, alias=alias)

    async def get_user(
        self, *, id_: UUID | None = None, alias: str | None = None, credentials: UserCredentialsEntity | None = None
    ) -> UserEntity:
        return await self.__users_interactor.get(id_=id_, alias=alias, credentials=credentials)

    async def get_message(self, chat: UUID, id_: UUID) -> MessageEntity:
        return await self.__messages_interactor.get(chat, id_)

    def filter_chats(
        self, *, updated_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[ChatEntity]:
        return self.__chats_interactor.filter(updated_before=updated_before, limit=limit)

    def filter_messages(
        self, chat: UUID, *, created_before: datetime | None = None, limit: int | None = None
    ) -> AsyncIterator[MessageEntity]:
        return self.__messages_interactor.filter(chat, created_before=created_before, limit=limit)

    async def create_chat(self, user: UUID, chat_entity: ChatEntity) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Create chat.
        await self.__chats_interactor.create(chat_entity)
        # Send event.
        await self.__events_interactor.publish(EventChatCreatedEntity(chat=chat_entity))

    async def create_user(self, user_credentials_entity: UserCredentialsEntity) -> UserEntity:
        user_entity = await self.__users_interactor.create(user_credentials_entity)
        await self.__publish_event(EventUserCreatedEntity(user=user_entity))
        return user_entity

    async def update_user(self, user_update_entity: UserUpdateEntity) -> UserEntity:
        user_entity = await self.__users_interactor.update(user_update_entity)
        await self.__publish_event(EventUserUpdatedEntity(user=user_entity))
        return user_entity

    async def delete_user(self, user: UUID) -> None:
        await self.__users_interactor.delete(user)
        await self.__publish_event(EventUserDeletedEntity(user=user))

    async def create_message(self, message_entity: MessageEntity) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=message_entity.author))
        # Update chat's updated_at.
        await self.__chats_interactor.update(message_entity.chat)
        # Create message.
        await self.__messages_interactor.create(message_entity)
        # Send event.
        await self.__publish_event(EventMessageCreatedEntity(message=message_entity))

    async def update_message(self, user: UUID, message_update_entity: MessageUpdateEntity) -> None:
        message_entity = await self.__messages_interactor.get(message_update_entity.id, message_update_entity.chat)

        if user != message_entity.author:
            message = "You have no permissions."
            raise MessagesUpdateError(message)

        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Update chat's updated_at.
        await self.__chats_interactor.update(message_update_entity.chat)
        # Update message.
        await self.__messages_interactor.update(message_update_entity)
        # Send event.
        await self.__publish_event(EventMessageUpdatedEntity(message=message_entity))

    async def delete_message(self, user: UUID, chat: UUID, message: UUID) -> None:
        message_entity = await self.__messages_interactor.get(chat, message)

        if user != message_entity.author:
            message_ = "You have no permissions."
            raise MessagesUpdateError(message_)

        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Update chat's updated_at.
        await self.__chats_interactor.update(chat)
        # Delete message.
        await self.__messages_interactor.delete(chat, message)
        # Send event.
        await self.__publish_event(EventMessageDeletedEntity(message=message))

    def subscribe_on_events(self) -> AsyncContextManager[AsyncIterator[EventEntity]]:
        return self.__events_interactor.subscribe()

    async def shutdown(self) -> None:
        await self.__users_interactor.shutdown()
        await self.__chats_interactor.shutdown()
        await self.__events_interactor.shutdown()
        await self.__messages_interactor.shutdown()

    async def __publish_event(self, entity: EventEntity) -> None:
        try:
            # Send event.
            await self.__events_interactor.publish(entity)

        except Exception as exception:
            message = f"Cannot sent event: {exception}"
            getLogger().exception(message)
