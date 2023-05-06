import pybase64
from pydantic import Field

from innonymous.presenters.api.domains.captcha.entities import CaptchaEntity
from innonymous.utils import FastPydanticBaseModel

__all__ = ("CaptchaSchema", "CaptchaSolvedSchema")


class CaptchaSchema(FastPydanticBaseModel):
    token: str = Field()
    image: str = Field()

    @classmethod
    def from_entity(cls, entity: CaptchaEntity) -> "CaptchaSchema":
        return cls(token=entity.token, image=f"data:image/jpeg;base64,{pybase64.b64encode(entity.image).decode()}")


class CaptchaSolvedSchema(FastPydanticBaseModel):
    token: str = Field()
    secret: str = Field()
