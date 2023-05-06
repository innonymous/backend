from typing import Protocol

import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserEntity, UserCredentialsEntity


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


@pytest.fixture
async def users_repository(mocker: MockFixture) -> UsersRepository:
    return mocker.Mock(UsersRepository)


@pytest.fixture
async def user_credentials() -> UserCredentialsEntity:
    return UserCredentialsEntity(alias="sus_guy127", password="strong_password")
