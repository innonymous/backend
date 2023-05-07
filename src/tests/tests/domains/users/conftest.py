import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserCredentialsEntity


@pytest.fixture
async def users_repository(mocker: MockFixture) -> UsersRepository:
    return mocker.Mock(UsersRepository)


@pytest.fixture
async def user_credentials() -> UserCredentialsEntity:
    return UserCredentialsEntity(alias="sus_guy127", password="strong_password")
