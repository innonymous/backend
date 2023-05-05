from pydantic import Field

from innonymous.utils import FastPydanticBaseModel

__all__ = ("UserSchema", "UserCredentialsSchema")


class UserSchema(FastPydanticBaseModel):
    pass


class UserCredentialsSchema(FastPydanticBaseModel):
    alias: str = Field()
    password: str = Field()
