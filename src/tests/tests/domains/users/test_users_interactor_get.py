import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersError, UsersNotFoundError
from innonymous.domains.users.interactors import UsersInteractor
from innonymous.domains.users.entities import UserCredentialsEntity, UserEntity

from tests.tests.domains.users.conftest import UserEntityProtocol

__all__ = ()


def is_same_user(expected: UserEntity, actual: UserEntity) -> bool:
    return expected.id == actual.id and expected.alias == actual.alias


@pytest.mark.user
class TestUsersInteractorGetMethod:
    async def test_by_id(
        self, mocker: MockFixture, user_entity_factory: UserEntityProtocol, users_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        get_method = mocker.patch.object(users_repository, "get", return_value=expected_user)

        interactor = UsersInteractor(users_repository)

        actual_user = await interactor.get(id_=expected_user.id)
        assert is_same_user(expected_user, actual_user)

        get_method.assert_called_with(id_=expected_user.id, alias=None)

    async def test_by_alias(
        self, mocker: MockFixture, user_entity_factory: UserEntityProtocol, users_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        get_method = mocker.patch.object(users_repository, "get", return_value=expected_user)

        interactor = UsersInteractor(users_repository)

        actual_user = await interactor.get(alias=expected_user.alias)
        assert is_same_user(expected_user, actual_user)

        get_method.assert_called_with(id_=None, alias=expected_user.alias)

    async def test_by_credentials(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        user_credentials: UserCredentialsEntity,
        users_repository: UsersRepository,
    ):
        mocker.patch.object(users_repository, "create")

        interactor = UsersInteractor(users_repository)
        expected_user = await interactor.create(user_credentials)

        get_method = mocker.patch.object(users_repository, "get", return_value=expected_user)

        actual_user = await interactor.get(credentials=user_credentials)
        assert is_same_user(expected_user, actual_user)

        get_method.assert_called_with(id_=None, alias=user_credentials.alias)

    async def test_fails_with_no_arguments(self, mocker: MockFixture, users_repository: UsersRepository) -> None:
        get_method = mocker.patch.object(users_repository, "get", side_effect=UsersError())

        interactor = UsersInteractor(users_repository)

        with pytest.raises(UsersError):
            _ = await interactor.get()

        get_method.assert_called_with(id_=None, alias=None)

    async def test_id_conflicts_with_alias(
        self, mocker: MockFixture, user_entity_factory: UserEntityProtocol, users_repository: UsersRepository
    ) -> None:
        expected_user = user_entity_factory()
        get_method = mocker.patch.object(users_repository, "get", side_effect=UsersError())

        interactor = UsersInteractor(users_repository)

        with pytest.raises(UsersError):
            _ = await interactor.get(id_=expected_user.id, alias=expected_user.alias)

        get_method.assert_called_with(id_=expected_user.id, alias=expected_user.alias)

    async def test_id_conflicts_with_credentials(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        user_credentials: UserCredentialsEntity,
        users_repository: UsersRepository,
    ) -> None:
        expected_user = user_entity_factory()
        get_method = mocker.patch.object(users_repository, "get", side_effect=UsersError())

        interactor = UsersInteractor(users_repository)

        with pytest.raises(UsersError):
            _ = await interactor.get(id_=expected_user.id, credentials=user_credentials)

        get_method.assert_called_with(id_=expected_user.id, alias=user_credentials.alias)

    async def test_user_not_found(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        user_credentials: UserCredentialsEntity,
        users_repository: UsersRepository,
    ) -> None:
        get_method = mocker.patch.object(users_repository, "get", return_value=None)

        some_user = user_entity_factory()
        interactor = UsersInteractor(users_repository)

        tasks_to_fail = [
            interactor.get(id_=some_user.id),
            interactor.get(alias=some_user.alias),
            interactor.get(credentials=user_credentials),
        ]
        for i, task in enumerate(tasks_to_fail):
            assert get_method.call_count == i
            with pytest.raises(UsersNotFoundError):
                await task
            assert get_method.call_count == i + 1
