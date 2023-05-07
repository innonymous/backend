from typing import Protocol

import pytest

from innonymous.domains.users.entities import UserEntity


class UserEntityProtocol(Protocol):
    def __call__(self, **fields) -> UserEntity:
        pass


@pytest.fixture
async def user_entity_factory() -> UserEntityProtocol:
    def factory(**fields) -> UserEntity:
        return UserEntity(
            **{  # type: ignore
                "salt": b"secret field",
                "payload": b"super secret field",
                "alias": "example_alias",
                **fields,
            }
        )

    return factory
