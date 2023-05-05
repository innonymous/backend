from typing import Any

import orjson
from pydantic import BaseModel

__all__ = ("FastPydanticBaseModel",)


def _orjson_dumps(*args: Any, **kwargs: Any) -> str:
    return orjson.dumps(*args, **kwargs).decode()


class FastPydanticBaseModel(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = _orjson_dumps
