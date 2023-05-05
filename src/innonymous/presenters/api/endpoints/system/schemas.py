from typing import Literal

from pydantic import Field

from innonymous.utils import FastPydanticBaseModel

__all__ = ("SystemStatusOKSchema",)


class SystemStatusOKSchema(FastPydanticBaseModel):
    status: Literal["ok"] = Field(default="ok")
