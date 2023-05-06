import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersError
from innonymous.domains.users.interactors import UsersInteractor

from .conftest import UserEntityProtocol


@pytest.mark.user
class TestUsersInteractorGetMethod:
    async def test_by_id(
            self,
            mocker: MockFixture,
            user_entity_factory: UserEntityProtocol,
            user_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        mocker.patch.object(user_repository, "get", return_value=expected_user)

        interactor = UsersInteractor(user_repository)

        actual_user = await interactor.get(id_=expected_user.id)
        assert expected_user == actual_user

    async def test_by_alias(
            self,
            mocker: MockFixture,
            user_entity_factory: UserEntityProtocol,
            user_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        mocker.patch.object(user_repository, "get", return_value=expected_user)

        interactor = UsersInteractor(user_repository)

        actual_user = await interactor.get(alias=expected_user.alias)
        assert expected_user == actual_user

    async def test_fails_with_no_arguments(
            self,
            mocker: MockFixture,
            user_repository: UsersRepository
    ) -> None:
        mocker.patch.object(user_repository, "get", side_effect=UsersError())

        interactor = UsersInteractor(user_repository)

        with pytest.raises(UsersError):
            _ = await interactor.get()

    async def test_id_conflicts_with_alias(
            self,
            mocker: MockFixture,
            user_entity_factory: UserEntityProtocol,
            user_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        mocker.patch.object(user_repository, "get", side_effect=UsersError())

        interactor = UsersInteractor(user_repository)

        with pytest.raises(UsersError):
            _ = await interactor.get(id_=expected_user.id, alias=expected_user.alias)
