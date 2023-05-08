from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from pytest_mock import MockFixture

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import UsersError

from tests.conftest import UserEntityProtocol
from tests.tests.data.repositories.user.conftest import StorageAndCollection

__all__ = ()


def user_entity_to_dict(user: UserEntity) -> dict[str, Any]:
    return {
        "salt": user.salt,
        "payload": user.payload,
        "alias": user.alias,
        "id": user.id.hex,
        "favorites": [id_.hex for id_ in user.favorites],
        "name": user.name,
        "about": user.about,
        "updated_at": user.updated_at,
    }


def assert_find_one_with_correct_query(call_args: tuple, expected_query: dict[str, Any]) -> None:
    args, _ = call_args
    actual_query, *_ = args

    assert expected_query == actual_query


@pytest.mark.mongo_repo
class TestMongoUsersRepositoryGetMethod:
    async def test_get_by_id(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
    ) -> None:
        current_time = datetime.now(tz=timezone.utc)
        some_user_id = uuid4()
        expected_user = user_entity_factory(
            salt="salt",
            payload="payload",
            alias="alias",
            id=some_user_id,
            favorites=[uuid4() for _ in range(5)],
            name="name",
            about="about",
            updated_at=current_time,
        )
        found_user = user_entity_to_dict(expected_user)
        expected_query = {"id": some_user_id.hex}

        mongodb_storage, mock_collection = user_storage_and_collection
        mock_collection.find_one = mocker.AsyncMock(return_value=found_user)

        repository = await UsersRepository(mongodb_storage)
        actual_user = await repository.get(id_=some_user_id)

        assert expected_user == actual_user
        mock_collection.find_one.assert_awaited_once()
        assert_find_one_with_correct_query(mock_collection.find_one.call_args, expected_query)

    async def test_get_by_alias(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
    ) -> None:
        current_time = datetime.now(tz=timezone.utc)
        some_alias = "some_alias"
        expected_user = user_entity_factory(
            salt="salt",
            payload="payload",
            alias=some_alias,
            id=uuid4(),
            favorites=[uuid4() for _ in range(5)],
            name="name",
            about="about",
            updated_at=current_time,
        )
        found_user = user_entity_to_dict(expected_user)
        expected_query = {"alias": some_alias}

        mongodb_storage, mock_collection = user_storage_and_collection
        mock_collection.find_one = mocker.AsyncMock(return_value=found_user)

        repository = await UsersRepository(mongodb_storage)
        actual_user = await repository.get(alias=some_alias)

        assert expected_user == actual_user
        mock_collection.find_one.assert_awaited_once()
        assert_find_one_with_correct_query(mock_collection.find_one.call_args, expected_query)

    async def test_get_id_conflicts_with_alias(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
    ) -> None:
        some_id = uuid4()
        some_alias = "some_alias"

        mongodb_storage, mock_collection = user_storage_and_collection
        mock_collection.find_one = mocker.AsyncMock()

        repository = await UsersRepository(mongodb_storage)
        with pytest.raises(UsersError):
            _ = await repository.get(id_=some_id, alias=some_alias)

        mock_collection.find_one.assert_not_awaited()

    async def test_get_returns_none_when_not_found(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
    ) -> None:
        unknown_id = uuid4()
        expected_query = {"id": unknown_id.hex}

        mongodb_storage, mock_collection = user_storage_and_collection
        mock_collection.find_one = mocker.AsyncMock(return_value=None)

        repository = await UsersRepository(mongodb_storage)
        actual_user = await repository.get(id_=unknown_id)

        assert actual_user is None
        mock_collection.find_one.assert_awaited_once()
        assert_find_one_with_correct_query(mock_collection.find_one.call_args, expected_query)
