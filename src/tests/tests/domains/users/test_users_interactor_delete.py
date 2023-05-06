import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersNotFoundError
from innonymous.domains.users.interactors import UsersInteractor

from .conftest import UserEntityProtocol


@pytest.mark.user
class TestUsersInteractorDeleteMethod:
    async def test_when_exists(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        users_repository: UsersRepository,
    ) -> None:
        user_to_delete = user_entity_factory()
        mocker.patch.object(users_repository, "delete", return_value=True)

        interactor = UsersInteractor(users_repository)
        await interactor.delete(user_to_delete.id)

        users_repository.delete.assert_called_with(user_to_delete.id)

    async def test_when_not_found(
        self,
        mocker: MockFixture,
        user_entity_factory: UserEntityProtocol,
        users_repository: UsersRepository,
    ) -> None:
        user_to_delete = user_entity_factory()
        mocker.patch.object(users_repository, "delete", return_value=False)

        interactor = UsersInteractor(users_repository)
        with pytest.raises(UsersNotFoundError):
            await interactor.delete(user_to_delete.id)

        users_repository.delete.assert_called_with(user_to_delete.id)
