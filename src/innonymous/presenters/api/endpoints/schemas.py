from typing import Any

from pydantic import Field

from innonymous.utils import FastPydanticBaseModel

__all__ = ("ErrorSchema",)


class ErrorSchema(FastPydanticBaseModel):
    alias: str = Field()
    attributes: dict[str, Any] = Field()
