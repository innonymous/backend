from dataclasses import asdict, is_dataclass
from typing import Any
from uuid import UUID


__all__ = ("as_dict",)


def as_dict(entity: Any) -> Any:
    if isinstance(entity, UUID):
        return entity.hex

    if is_dataclass(entity):
        return {field: as_dict(value) for field, value in asdict(entity).items()}

    if isinstance(entity, dict):
        return {field: as_dict(value) for field, value in entity.items()}

    if isinstance(entity, list):
        return [as_dict(value) for value in entity]

    if isinstance(entity, tuple):
        return tuple(as_dict(value) for value in entity)

    return entity
