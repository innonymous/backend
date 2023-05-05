from enum import Enum

__all__ = ("EventType",)


class EventType(str, Enum):
    CHAT_CREATED = "chat_created"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    MESSAGE_CREATED = "message_created"
    MESSAGE_UPDATED = "message_updated"
    MESSAGE_DELETED = "message_deleted"
