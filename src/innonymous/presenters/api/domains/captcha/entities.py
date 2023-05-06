from pydantic import Field
from pydantic.dataclasses import dataclass

__all__ = ("CaptchaEntity", "CaptchaSolvedEntity")


@dataclass
class CaptchaEntity:
    token: str = Field()
    image: bytes = Field()


@dataclass
class CaptchaSolvedEntity:
    token: str = Field()
    secret: str = Field()
