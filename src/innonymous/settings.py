from pydantic import BaseSettings, Field, MongoDsn

__all__ = ("Settings",)


class Settings(BaseSettings):
    DATABASE_URL: MongoDsn = Field(default="mongodb://innonymous:innonymous@localhost")
    DATABASE_NAME: str = Field(default="innonymous")

    class Config:
        case_sensitive = False

        env_file = "./.env"
        env_prefix = "INNONYMOUS_"
