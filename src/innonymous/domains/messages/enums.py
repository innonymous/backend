from enum import Enum

__all__ = ("MessageType",)


class MessageType(str, Enum):
    TEXT = "text"
    FILES = "files"
