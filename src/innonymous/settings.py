from datetime import timedelta

from pydantic import BaseSettings, Field, MongoDsn

__all__ = ("Settings",)


class Settings(BaseSettings):
    DATABASE_URL: MongoDsn = Field(default="mongodb://innonymous:innonymous@localhost")
    MAIN_DATABASE_NAME: str = Field(default="innonymous-main")
    MESSAGES_DATABASE_NAME: str = Field(default="innonymous-chats")

    USERS_COLLECTION_NAME: str = Field(default="users")
    CHATS_COLLECTION_NAME: str = Field(default="chats")
    MESSAGES_COLLECTION_PREFIX: str = Field(default="chat")

    USERS_TTL: timedelta = Field(default=timedelta(days=30))
    CHATS_TTL: timedelta = Field(default=timedelta(days=30))
    MESSAGES_TTL: timedelta = Field(default=timedelta(days=30))

    class Config:
        case_sensitive = False

        env_file = "./.env"
        env_prefix = "INNONYMOUS_"
