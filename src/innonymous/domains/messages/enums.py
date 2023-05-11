from enum import Enum

__all__ = ("MessageType", "MessageFragmentType", "MessageFragmentMentionType", "MessageFragmentTextStyle")


class MessageType(str, Enum):
    TEXT = "text"
    FILES = "files"


class MessageFragmentType(str, Enum):
    TEXT = "text"
    LINK = "link"
    MENTION = "mention"


class MessageFragmentMentionType(str, Enum):
    USER = "user"
    CHAT = "chat"
    MESSAGE = "message"


class MessageFragmentTextStyle(str, Enum):
    BOLD = "bold"
    NORMAL = "normal"
    ITALIC = "italic"
    MONOSPACE = "monospace"
    STRIKETHROUGH = "strikethrough"
