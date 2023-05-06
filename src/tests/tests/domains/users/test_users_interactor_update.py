from uuid import uuid4
from datetime import datetime, timezone

import pytest
from pytest_mock import MockFixture
from freezegun import freeze_time

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersNotFoundError, UsersAlreadyExistsError
from innonymous.domains.users.interactors import UsersInteractor
from innonymous.domains.users.entities import UserUpdateEntity

from .conftest import UserEntityProtocol


@pytest.mark.user
@freeze_time(datetime(year=2023, month=5, day=6))
class TestUsersInteractorUpdateMethod:
    async def test_update_all_fields(
            self,
            mocker: MockFixture,
            user_entity_factory: UserEntityProtocol,
            users_repository: UsersRepository,
    ) -> None:
        original_user = user_entity_factory()
        expected_updated_user = user_entity_factory(
            id=original_user.id,
            favorites=[uuid4()],
            name="new name",
            alias="new_alias",
            about="new about",
            updated_at=datetime.now(tz=timezone.utc)
        )

        mocker.patch.object(users_repository, "get", return_value=original_user)
        mocker.patch.object(users_repository, "update")

        user_update_entity = UserUpdateEntity(
            id=original_user.id,
            favorites=expected_updated_user.favorites,
            name=expected_updated_user.name,
            alias=expected_updated_user.alias,
            about=expected_updated_user.about,
            password="new_password123"
        )

        interactor = UsersInteractor(users_repository)
        actual_updated_user = await interactor.update(user_update_entity)

        users_repository.update.assert_called_once()

        assert original_user.id == expected_updated_user.id == actual_updated_user.id

        assert original_user.salt != actual_updated_user.salt
        assert original_user.payload != actual_updated_user.payload

        assert expected_updated_user.alias == actual_updated_user.alias
        assert expected_updated_user.favorites == actual_updated_user.favorites
        assert expected_updated_user.name == actual_updated_user.name
        assert expected_updated_user.about == actual_updated_user.about
        assert expected_updated_user.updated_at == actual_updated_user.updated_at

    async def test_user_already_exists(
            self,
            mocker: MockFixture,
            user_entity_factory: UserEntityProtocol,
            users_repository: UsersRepository
    ) -> None:
        original_user = user_entity_factory()
        mocker.patch.object(users_repository, "get", return_value=original_user)
        mocker.patch.object(users_repository, "update", side_effect=UsersAlreadyExistsError())

        user_update_entity = UserUpdateEntity(
            id=original_user.id,
            alias="duplicate"
        )

        interactor = UsersInteractor(users_repository)
        with pytest.raises(UsersAlreadyExistsError):
            _ = await interactor.update(user_update_entity)

        users_repository.update.assert_called_once()

    async def test_original_user_not_found(
            self,
            mocker: MockFixture,
            users_repository: UsersRepository
    ) -> None:
        mocker.patch.object(users_repository, "get", side_effect=UsersNotFoundError)
        mocker.patch.object(users_repository, "update")

        user_update_entity = UserUpdateEntity(
            id=uuid4()
        )

        interactor = UsersInteractor(users_repository)
        with pytest.raises(UsersNotFoundError):
            _ = await interactor.update(user_update_entity)

        users_repository.update.assert_not_called()
