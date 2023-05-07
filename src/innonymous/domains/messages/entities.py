from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import AnyUrl, Field, validator
from pydantic.dataclasses import dataclass

from innonymous.domains.messages.enums import (
    MessageFragmentMentionType,
    MessageFragmentTextStyle,
    MessageFragmentType,
    MessageType,
)

__all__ = (
    "MessageTextBodyEntity",
    "MessageFilesBodyEntity",
    "MessageEntity",
    "MessageUpdateEntity",
    "MESSAGE_MAX_CHARACTERS",
    "MessageFragmentMentionUserEntity",
    "MessageFragmentMentionChatEntity",
    "MessageFragmentMentionMessageEntity",
    "MessageFragmentMentionEntity",
    "MessageFragmentTextEntity",
    "MessageFragmentLinkEntity",
    "MessageFragmentEntity",
)


MESSAGE_MAX_CHARACTERS = 1024


@dataclass
class MessageFragmentMentionUserEntity:
    user: UUID = Field()
    type: Literal[MessageFragmentMentionType.USER] = Field(default=MessageFragmentMentionType.USER)  # noqa: A003


@dataclass
class MessageFragmentMentionChatEntity:
    chat: UUID = Field()
    type: Literal[MessageFragmentMentionType.CHAT] = Field(default=MessageFragmentMentionType.CHAT)  # noqa: A003


@dataclass
class MessageFragmentMentionMessageEntity:
    chat: UUID = Field()
    message: UUID = Field()
    type: Literal[MessageFragmentMentionType.MESSAGE] = Field(default=MessageFragmentMentionType.MESSAGE)  # noqa: A003


@dataclass
class MessageFragmentMentionEntity:
    # fmt: off
    mention: MessageFragmentMentionUserEntity \
             | MessageFragmentMentionChatEntity \
             | MessageFragmentMentionMessageEntity = Field(discriminator="type")
    # fmt: on
    type: Literal[MessageFragmentType.MENTION] = Field(default=MessageFragmentType.MENTION)  # noqa: A003


@dataclass
class MessageFragmentTextEntity:
    text: str = Field(min_length=1)
    style: MessageFragmentTextStyle = Field(default=MessageFragmentTextStyle.NORMAL)
    type: Literal[MessageFragmentType.TEXT] = Field(default=MessageFragmentType.TEXT)  # noqa: A003


@dataclass
class MessageFragmentLinkEntity:
    link: AnyUrl = Field()
    text: str | None = Field(default=None, min_length=1)
    type: Literal[MessageFragmentType.LINK] = Field(default=MessageFragmentType.LINK)  # noqa: A003


MessageFragmentEntity = Annotated[
    MessageFragmentTextEntity | MessageFragmentLinkEntity | MessageFragmentMentionEntity,
    Field(discriminator="type"),
]


def _validate_fragments(fragments: list[MessageFragmentEntity]) -> list[MessageFragmentEntity]:
    length = 0

    for fragment in fragments:
        if isinstance(fragment, MessageFragmentTextEntity):
            length += len(fragment.text)

        elif isinstance(fragment, MessageFragmentLinkEntity):
            length += len(fragment.link) if fragment.text is None else len(fragment.text)

        elif isinstance(fragment, MessageFragmentMentionEntity):
            if isinstance(fragment.mention, MessageFragmentMentionUserEntity | MessageFragmentMentionChatEntity):
                length += 64

            elif isinstance(fragment.mention, MessageFragmentMentionMessageEntity):
                length += 96

        if length > MESSAGE_MAX_CHARACTERS:
            message = "Max length of the message is 1024 characters."
            raise ValueError(message)

    return fragments


@dataclass
class MessageTextBodyEntity:
    fragments: list[MessageFragmentEntity] = Field(min_items=1)
    type: Literal[MessageType.TEXT] = Field(default=MessageType.TEXT)  # noqa: A003

    @validator("fragments", always=True)
    def __validate_fragments(cls, fragments: list[MessageFragmentEntity]) -> list[MessageFragmentEntity]:
        return _validate_fragments(fragments)


@dataclass
class MessageFilesBodyEntity:
    files: list[UUID] = Field(min_items=1, max_items=10)
    fragments: list[MessageFragmentEntity] = Field(default=[])
    type: Literal[MessageType.FILES] = Field(default=MessageType.FILES)  # noqa: A003

    @validator("fragments", always=True)
    def __validate_fragments(cls, fragments: list[MessageFragmentEntity]) -> list[MessageFragmentEntity]:
        return _validate_fragments(fragments)


@dataclass
class MessageEntity:
    chat: UUID = Field()
    author: UUID = Field()
    body: MessageTextBodyEntity | MessageFilesBodyEntity = Field(discriminator="type")
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    replied_to: UUID | None = Field(default=None)
    forwarded_from: UUID | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @validator("updated_at", "created_at", always=True)
    def __validate_datetime(cls, value: datetime) -> datetime:
        return value.astimezone(tz=timezone.utc)


@dataclass
class MessageUpdateEntity:
    id: UUID = Field()  # noqa: A003
    chat: UUID = Field()
    body: MessageTextBodyEntity | MessageFilesBodyEntity | None = Field(default=None, discriminator="type")
