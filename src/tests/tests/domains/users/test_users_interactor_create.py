import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersAlreadyExistsError
from innonymous.domains.users.entities import UserEntity, UserCredentialsEntity
from innonymous.domains.users.interactors import UsersInteractor

from .conftest import UserEntityProtocol


@pytest.mark.user
class TestUsersInteractorCreateMethod:
    async def test_successful(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        user_credentials: UserCredentialsEntity,
        users_repository: UsersRepository,
    ) -> None:
        expected_user = user_entity_factory(alias=user_credentials.alias)

        def check_if_alias_matches(created_user: UserEntity) -> None:
            assert expected_user.alias == created_user.alias

        mocker.patch.object(users_repository, "create", side_effect=check_if_alias_matches)

        interactor = UsersInteractor(users_repository)
        actual_user = await interactor.create(user_credentials)

        assert expected_user.alias == actual_user.alias

    async def test_user_already_exists(
        self, mocker: MockFixture, user_credentials: UserCredentialsEntity, users_repository: UsersRepository
    ) -> None:
        mocker.patch.object(users_repository, "create", side_effect=UsersAlreadyExistsError())

        interactor = UsersInteractor(users_repository)

        with pytest.raises(UsersAlreadyExistsError):
            _ = await interactor.create(user_credentials)
