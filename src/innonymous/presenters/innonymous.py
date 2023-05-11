import re
from contextlib import suppress
from datetime import datetime
from logging import getLogger
from typing import Any, AsyncContextManager, AsyncIterator, Sequence, Sized, TypeAlias
from uuid import UUID

from pydantic import ValidationError

from innonymous.data.repositories.chats import ChatsRepository
from innonymous.data.repositories.events import EventsRepository
from innonymous.data.repositories.messages import MessagesRepository
from innonymous.data.repositories.sessions import SessionsRepository
from innonymous.data.repositories.users import UsersRepository
from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.data.storages.rabbitmq import RabbitMQStorage
from innonymous.domains.chats.entities import ChatEntity
from innonymous.domains.chats.errors import ChatsAlreadyExistsError, ChatsNotFoundError
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
from innonymous.domains.messages.entities import (
    MessageCreateEntity,
    MessageEntity,
    MessageFragmentLinkEntity,
    MessageFragmentMentionChatEntity,
    MessageFragmentMentionEntity,
    MessageFragmentMentionMessageEntity,
    MessageFragmentMentionUserEntity,
    MessageFragmentTextEntity,
    MessageUpdateEntity,
)
from innonymous.domains.messages.enums import MessageFragmentTextStyle
from innonymous.domains.messages.errors import MessagesUpdateError
from innonymous.domains.messages.interactors import MessagesInteractor
from innonymous.domains.sessions.entities import SessionEntity
from innonymous.domains.sessions.interactors import SessionsInteractor
from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity, UserUpdateEntity
from innonymous.domains.users.errors import UsersAlreadyExistsError, UsersNotFoundError
from innonymous.domains.users.interactors import UsersInteractor
from innonymous.settings import Settings
from innonymous.utils import AsyncLazyObject

__all__ = ("Innonymous",)


Fragment: TypeAlias = str | MessageFragmentMentionEntity | MessageFragmentLinkEntity | MessageFragmentTextEntity


class Innonymous(AsyncLazyObject):
    __BOLD_TEXT_PATTERN = re.compile(r"\*\*((.|\n)+)\*\*")
    __ITALIC_TEXT_PATTERN = re.compile(r"__((.|\n)+)__")
    __MONOSPACE_TEXT_PATTERN = re.compile(r"```((.|\n)+)```")
    __STRIKETHROUGH_TEXT_PATTERN = re.compile(r"~~((.|\n)+)~~")
    __MENTION_PATTERN = re.compile(r"(^|\s)@[a-zA-Z0-9]\w{3,30}[a-zA-Z0-9](\s|$)")
    __MESSAGE_MENTION_PATTERN = re.compile(
        r"(^|\s)@([a-zA-Z0-9]\w{3,30}[a-zA-Z0-9])\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-f"
        r"A-F]{12})(\s|$)"
    )
    __URL_WITH_TEXT_PATTERN = re.compile(
        r"\[(.+)\]\(\s*((?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:\/?#[\]@!\$&'\(\)\*\+,;=.]+)\s*\)"
    )
    __URL_WITHOUT_TEXT_PATTERN = re.compile(
        r"(^|\s)((?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:\/?#[\]@!\$&'\(\)\*\+,;=.]+)(\s|$)"
    )

    async def __ainit__(self, *, settings: Settings | None = None) -> None:
        self.__settings = Settings() if settings is None else settings
        main_mongodb_storage = await MongoDBStorage(self.__settings.DATABASE_URL, db=self.__settings.MAIN_DATABASE_NAME)

        self.__users_interactor = UsersInteractor(
            await UsersRepository(
                main_mongodb_storage, collection=self.__settings.USERS_COLLECTION_NAME, ttl=self.__settings.USERS_TTL
            )
        )
        self.__sessions_interactor = SessionsInteractor(
            await SessionsRepository(
                main_mongodb_storage,
                collection=self.__settings.SESSIONS_COLLECTION_NAME,
                ttl=self.__settings.SESSIONS_TTL,
            )
        )
        self.__chats_interactor = ChatsInteractor(
            await ChatsRepository(
                main_mongodb_storage, collection=self.__settings.CHATS_COLLECTION_NAME, ttl=self.__settings.CHATS_TTL
            )
        )
        self.__events_interactor = EventsInteractor(
            EventsRepository(
                await RabbitMQStorage(self.__settings.BROKER_URL, exchange=self.__settings.BROKER_EXCHANGE)
            )
        )
        self.__messages_interactor = MessagesInteractor(
            await MessagesRepository(
                await MongoDBStorage(self.__settings.DATABASE_URL, db=self.__settings.MESSAGES_DATABASE_NAME),
                collections_prefix=self.__settings.MESSAGES_COLLECTION_PREFIX,
                ttl=self.__settings.MESSAGES_TTL,
            ),
        )

    async def get_user(
        self, *, id_: UUID | None = None, alias: str | None = None, credentials: UserCredentialsEntity | None = None
    ) -> UserEntity:
        return await self.__users_interactor.get(id_=id_, alias=alias, credentials=credentials)

    def filter_users(
        self,
        *,
        search: str | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[UserEntity]:
        return self.__users_interactor.filter(
            search=search, updated_after=updated_after, updated_before=updated_before, limit=limit
        )

    async def create_user(self, user_credentials_entity: UserCredentialsEntity) -> UserEntity:
        with suppress(ChatsNotFoundError):
            chat = await self.get_chat(alias=user_credentials_entity.alias)
            raise ChatsAlreadyExistsError(id_=chat.id, alias=chat.alias)

        user_entity = await self.__users_interactor.create(user_credentials_entity)
        await self.__publish_event(EventUserCreatedEntity(user=user_entity))
        return user_entity

    async def update_user(self, user_update_entity: UserUpdateEntity) -> UserEntity:
        user_entity = await self.__users_interactor.update(user_update_entity)

        if (
            user_update_entity.alias is not None
            or user_update_entity.about is not None
            or user_update_entity.name is not None
        ):
            await self.__publish_event(EventUserUpdatedEntity(user=user_entity))

        return user_entity

    async def delete_user(self, user: UUID) -> None:
        await self.__users_interactor.delete(user)
        await self.__sessions_interactor.delete(user=user)
        await self.__publish_event(EventUserDeletedEntity(user=user))

    async def get_session(self, id_: UUID) -> SessionEntity:
        return await self.__sessions_interactor.get(id_)

    def filter_sessions(self, *, user: UUID | None = None) -> AsyncIterator[SessionEntity]:
        return self.__sessions_interactor.filter(user=user)

    async def create_session(self, session_entity: SessionEntity) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=session_entity.user))
        # Create session.
        await self.__sessions_interactor.create(session_entity)

    async def update_session(self, user: UUID, session: UUID) -> SessionEntity:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Update session.
        return await self.__sessions_interactor.update(session)

    async def delete_session(self, user: UUID, *, session: UUID | None = None) -> None:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Delete one or all sessions.
        kwargs = {"user": user} if session is None else {"id_": session}
        await self.__sessions_interactor.delete(**kwargs)

    async def get_chat(self, *, id_: UUID | None = None, alias: str | None = None) -> ChatEntity:
        return await self.__chats_interactor.get(id_=id_, alias=alias)

    def filter_chats(
        self,
        *,
        search: str | None = None,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[ChatEntity]:
        return self.__chats_interactor.filter(
            search=search, updated_after=updated_after, updated_before=updated_before, limit=limit
        )

    async def create_chat(self, user: UUID, chat_entity: ChatEntity) -> None:
        with suppress(UsersNotFoundError):
            user_entity = await self.get_user(alias=chat_entity.alias)
            raise UsersAlreadyExistsError(id_=user_entity.id, alias=user_entity.alias)

        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Create chat.
        await self.__chats_interactor.create(chat_entity)
        # Send event.
        await self.__events_interactor.publish(EventChatCreatedEntity(chat=chat_entity))

    def subscribe_on_events(self) -> AsyncContextManager[AsyncIterator[EventEntity]]:
        return self.__events_interactor.subscribe()

    async def get_message(self, chat: UUID, id_: UUID) -> MessageEntity:
        return await self.__messages_interactor.get(chat, id_)

    def filter_messages(
        self,
        chat: UUID,
        *,
        search: str | None = None,
        author: UUID | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[MessageEntity]:
        return self.__messages_interactor.filter(
            chat, search=search, author=author, created_after=created_after, created_before=created_before, limit=limit
        )

    async def create_message(self, entity: MessageCreateEntity) -> MessageEntity:
        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=entity.author))
        # Update chat's updated_at.
        await self.__chats_interactor.update(entity.chat)
        # Create message.
        message_entity = await self.__messages_interactor.create(entity)
        # Send event.
        await self.__publish_event(EventMessageCreatedEntity(message=message_entity))
        return message_entity

    async def update_message(self, user: UUID, message_update_entity: MessageUpdateEntity) -> MessageEntity:
        old_message_entity = await self.__messages_interactor.get(message_update_entity.chat, message_update_entity.id)

        if user != old_message_entity.author:
            message = "You have no permissions."
            raise MessagesUpdateError(message)

        # Update user's updated_at.
        await self.__users_interactor.update(UserUpdateEntity(id=user))
        # Update chat's updated_at.
        await self.__chats_interactor.update(message_update_entity.chat)
        # Update message.
        new_message_entity = await self.__messages_interactor.update(message_update_entity)
        # Send event.
        await self.__publish_event(EventMessageUpdatedEntity(message=new_message_entity))
        return new_message_entity

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

    async def shutdown(self) -> None:
        await self.__users_interactor.shutdown()
        await self.__chats_interactor.shutdown()
        await self.__events_interactor.shutdown()
        await self.__sessions_interactor.shutdown()
        await self.__messages_interactor.shutdown()

    async def string_to_fragments(
        self, string: str
    ) -> list[MessageFragmentMentionEntity | MessageFragmentLinkEntity | MessageFragmentTextEntity]:
        is_changed = True
        fragments: list[Fragment] = [string]

        while is_changed:
            is_changed, fragments = await self.__try_parse(fragments)

        result = []
        for fragment in fragments:
            if not isinstance(fragment, str):
                result.append(fragment)
                continue

            text = fragment.strip()
            if len(text) > 1:
                result.append(MessageFragmentTextEntity(text=text))

        return result

    @staticmethod
    def __append_if_not_empty(value: Sized, target: list[Any]) -> bool:
        if len(value) > 0:
            target.append(value)
            return True

        return False

    @classmethod
    def __try_parse_url_with_text(cls, fragment: str, fragments: list[Fragment]) -> bool:
        match = cls.__URL_WITH_TEXT_PATTERN.search(fragment)

        if match is None:
            return False

        # Use https by default.
        url = match.group(2).strip()
        if not url.startswith("http"):
            url = "https://" + url

        try:
            entity = MessageFragmentLinkEntity(link=url, text=match.group(1).strip())  # type: ignore[arg-type]

        except ValidationError:
            return False

        cls.__append_if_not_empty(fragment[: match.start()], fragments)
        fragments.append(entity)
        cls.__append_if_not_empty(fragment[match.end() :], fragments)

        return True

    @classmethod
    def __try_parse_url_without_text(cls, fragment: str, fragments: list[Fragment]) -> bool:
        match = cls.__URL_WITHOUT_TEXT_PATTERN.search(fragment)

        if match is None:
            return False

        # Use https by default.
        url = match.group().strip()
        if not url.startswith("http"):
            url = "https://" + url

        try:
            entity = MessageFragmentLinkEntity(link=url)  # type: ignore[arg-type]

        except ValidationError:
            return False

        cls.__append_if_not_empty(fragment[: match.start()], fragments)
        fragments.append(entity)
        cls.__append_if_not_empty(fragment[match.end() :], fragments)

        return True

    @classmethod
    def __try_parse_text(cls, fragment: str, fragments: list[Fragment]) -> bool:
        for pattern, style in (
            (cls.__BOLD_TEXT_PATTERN, MessageFragmentTextStyle.BOLD),
            (cls.__ITALIC_TEXT_PATTERN, MessageFragmentTextStyle.ITALIC),
            (cls.__MONOSPACE_TEXT_PATTERN, MessageFragmentTextStyle.MONOSPACE),
            (cls.__STRIKETHROUGH_TEXT_PATTERN, MessageFragmentTextStyle.STRIKETHROUGH),
        ):
            match = pattern.search(fragment)

            if match is None:
                continue

            try:
                entity = MessageFragmentTextEntity(text=match.group(1).strip(), style=style)

            except ValidationError:
                continue

            cls.__append_if_not_empty(fragment[: match.start()], fragments)
            fragments.append(entity)
            cls.__append_if_not_empty(fragment[match.end() :], fragments)

            return True

        return False

    async def __try_parse_mention(self, fragment: str, fragments: list[Fragment]) -> bool:
        match = self.__MENTION_PATTERN.search(fragment)

        if match is None:
            return False

        mention: MessageFragmentMentionUserEntity | MessageFragmentMentionChatEntity | None = None

        try:
            # Check if this is users.
            user = await self.get_user(alias=match.group().strip()[1:])
            mention = MessageFragmentMentionUserEntity(user=user.id)

        except UsersNotFoundError:
            try:
                # Check if this is chat.
                chat = await self.get_chat(alias=match.group().strip()[1:])
                mention = MessageFragmentMentionChatEntity(chat=chat.id)

            except ChatsNotFoundError:
                pass

        if mention is None:
            return False

        self.__append_if_not_empty(fragment[: match.start()], fragments)
        fragments.append(MessageFragmentMentionEntity(mention=mention))
        self.__append_if_not_empty(fragment[match.end() :], fragments)

        return True

    async def __try_parse_message_mention(self, fragment: str, fragments: list[Fragment]) -> bool:
        match = self.__MESSAGE_MENTION_PATTERN.search(fragment)

        if match is None:
            return False

        try:
            # Check if this is chat.
            chat = await self.get_chat(alias=match.group(2).strip())
            mention = MessageFragmentMentionMessageEntity(chat=chat.id, message=UUID(match.group(3).strip()))

        except (ChatsNotFoundError, ValueError):
            return False

        self.__append_if_not_empty(fragment[: match.start()], fragments)
        fragments.append(MessageFragmentMentionEntity(mention=mention))
        self.__append_if_not_empty(fragment[match.end() :], fragments)

        return True

    async def __try_parse(
        self,
        fragments: Sequence[Fragment],
    ) -> tuple[bool, list[Fragment]]:
        is_changed = False

        updated_fragments: list[Fragment] = []
        for fragment in fragments:
            if not isinstance(fragment, str):
                updated_fragments.append(fragment)
                continue

            if self.__try_parse_url_with_text(fragment, updated_fragments):
                is_changed = True
                continue

            if self.__try_parse_url_without_text(fragment, updated_fragments):
                is_changed = True
                continue

            if await self.__try_parse_message_mention(fragment, updated_fragments):
                is_changed = True
                continue

            if await self.__try_parse_mention(fragment, updated_fragments):
                is_changed = True
                continue

            if self.__try_parse_text(fragment, updated_fragments):
                is_changed = True
                continue

            # No success.
            updated_fragments.append(fragment)

        merged_fragments: list[Fragment] = []
        for fragment in updated_fragments:
            if len(merged_fragments) == 0 or not isinstance(fragment, str) or not isinstance(merged_fragments[-1], str):
                merged_fragments.append(fragment)
                continue

            merged_fragments[-1] += fragment
            is_changed = True

        return is_changed, merged_fragments

    async def __publish_event(self, entity: EventEntity) -> None:
        try:
            # Send event.
            await self.__events_interactor.publish(entity)

        except Exception as exception:
            message = f"Cannot sent event: {exception}"
            getLogger().exception(message)
