from uuid import uuid4
from datetime import datetime, timezone
from typing import Any

import pytest
from pytest_mock import MockFixture
from freezegun import freeze_time

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.errors import UsersNotFoundError, UsersAlreadyExistsError
from innonymous.domains.users.interactors import UsersInteractor
from innonymous.domains.users.entities import UserUpdateEntity, UserEntity

from tests.tests.domains.users.conftest import UserEntityProtocol

__all__ = ()


def unpack_call_args(call_args: tuple) -> tuple[UserEntity, datetime]:
    args, kwargs = call_args
    new_user_entity, *_ = args
    return new_user_entity, kwargs["updated_at"]


def assert_successful_update_with_correct_args(call_args: tuple, expected: dict[str, Any]) -> None:
    new_user_entity, updated_at = unpack_call_args(call_args)

    assert expected["old_updated_at"] == updated_at

    assert expected["id"] == new_user_entity.id
    assert expected["favorites"] == new_user_entity.favorites
    assert expected["name"] == new_user_entity.name
    assert expected["alias"] == new_user_entity.alias
    assert expected["about"] == new_user_entity.about
    assert new_user_entity.salt is not None
    assert new_user_entity.payload is not None


def assert_duplicate_alias_with_correct_args(call_args: tuple, expected: dict[str, Any]):
    new_user_entity, updated_at = unpack_call_args(call_args)

    assert expected["old_updated_at"] == updated_at

    assert expected["id"] == new_user_entity.id
    assert expected["alias"] == new_user_entity.alias
    assert expected["salt"] == new_user_entity.salt
    assert expected["payload"] == new_user_entity.payload


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
            updated_at=datetime.now(tz=timezone.utc),
        )

        mocker.patch.object(users_repository, "get", return_value=original_user)
        mocker.patch.object(users_repository, "update")

        user_update_entity = UserUpdateEntity(
            id=original_user.id,
            favorites=expected_updated_user.favorites,
            name=expected_updated_user.name,
            alias=expected_updated_user.alias,
            about=expected_updated_user.about,
            password="new_password123",
        )

        interactor = UsersInteractor(users_repository)
        actual_updated_user = await interactor.update(user_update_entity)

        assert original_user.id == expected_updated_user.id == actual_updated_user.id

        assert original_user.salt != actual_updated_user.salt
        assert original_user.payload != actual_updated_user.payload

        assert expected_updated_user.alias == actual_updated_user.alias
        assert expected_updated_user.favorites == actual_updated_user.favorites
        assert expected_updated_user.name == actual_updated_user.name
        assert expected_updated_user.about == actual_updated_user.about
        assert expected_updated_user.updated_at == actual_updated_user.updated_at

        assert_successful_update_with_correct_args(
            users_repository.update.call_args,
            {
                "old_updated_at": original_user.updated_at,
                "id": original_user.id,
                "favorites": expected_updated_user.favorites,
                "name": expected_updated_user.name,
                "alias": expected_updated_user.alias,
                "about": expected_updated_user.about,
            },
        )

    async def test_user_already_exists(
        self, mocker: MockFixture, user_entity_factory: UserEntityProtocol, users_repository: UsersRepository
    ) -> None:
        original_user = user_entity_factory()
        mocker.patch.object(users_repository, "get", return_value=original_user)
        mocker.patch.object(users_repository, "update", side_effect=UsersAlreadyExistsError())

        user_update_entity = UserUpdateEntity(id=original_user.id, alias="duplicate")

        interactor = UsersInteractor(users_repository)
        with pytest.raises(UsersAlreadyExistsError):
            _ = await interactor.update(user_update_entity)

        assert_duplicate_alias_with_correct_args(
            users_repository.update.call_args,
            {
                "id": original_user.id,
                "alias": user_update_entity.alias,
                "salt": original_user.salt,
                "payload": original_user.payload,
                "old_updated_at": original_user.updated_at,
            },
        )

    async def test_original_user_not_found(self, mocker: MockFixture, users_repository: UsersRepository) -> None:
        mocker.patch.object(users_repository, "get", side_effect=UsersNotFoundError())
        mocker.patch.object(users_repository, "update")

        user_update_entity = UserUpdateEntity(id=uuid4())

        interactor = UsersInteractor(users_repository)
        with pytest.raises(UsersNotFoundError):
            _ = await interactor.update(user_update_entity)

        users_repository.update.assert_not_called()
