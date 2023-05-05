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
    EventMessageCreatedEntity,
    EventMessageDeletedEntity,
    EventMessageUpdatedEntity,
)
from innonymous.domains.events.interactors import EventsInteractor
from innonymous.domains.messages.entities import MessageEntity, MessageUpdateEntity
from innonymous.domains.messages.errors import MessagesUpdateError
from innonymous.domains.messages.interactors import MessagesInteractor
from innonymous.domains.users.entities import UserUpdateEntity
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
                collection_prefix=settings.MESSAGES_COLLECTION_PREFIX,
                ttl=settings.MESSAGES_TTL,
            ),
        )

    async def create_chat(self, user: UUID, chat_entity: ChatEntity) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Create chat.
        await self.__chats_interactor.create(chat_entity)
        # Send event.
        await self.__events_interactor.publish(EventChatCreatedEntity(chat=chat_entity))

    async def create_message(self, message_entity: MessageEntity) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=message_entity.author))
        # Update chat's updated_at.
        await self.__chats_interactor.update(message_entity.chat)
        # Create message.
        await self.__messages_interactor.create(message_entity)
        # Send event.
        await self.__events_interactor.publish(EventMessageCreatedEntity(message=message_entity))

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
        await self.__events_interactor.publish(EventMessageUpdatedEntity(message=message_entity))

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
        await self.__events_interactor.publish(EventMessageDeletedEntity(message=message))

    async def shutdown(self) -> None:
        await self.__users_interactor.shutdown()
        await self.__chats_interactor.shutdown()
        await self.__events_interactor.shutdown()
        await self.__messages_interactor.shutdown()
