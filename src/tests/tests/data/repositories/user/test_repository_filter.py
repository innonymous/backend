import operator
from datetime import datetime, timezone, timedelta
from typing import Callable, Any
from uuid import uuid4

import pytest
import pytest_freezegun
from pytest_mock import MockFixture
from pytest_freezegun import freeze_time
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorCursor

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import UsersAlreadyExistsError

from tests.conftest import UserEntityProtocol
from tests.tests.data.repositories.user.conftest import StorageAndCollection

__all__ = ()

SearchQuery = dict[str, Any]
SortQuery = list[tuple[str, Any]]
ProjectionQuery = dict[str, dict[str, Any]] | None


@pytest.fixture
async def mock_motor_cursor_factory(mocker: MockFixture) -> Callable:
    def factory(items_to_iterate: list):
        async def mock_async_iterator():
            for item in items_to_iterate:
                yield item

        mock_cursor = mocker.MagicMock(spec=AsyncIOMotorCursor)
        mock_cursor.__aiter__ = mocker.Mock(return_value=mock_async_iterator().__aiter__())
        return mock_cursor

    return factory


def user_entity_to_dict(user: UserEntity) -> dict[str, Any]:
    return {
        "salt": user.salt,
        "payload": user.payload,
        "alias": user.alias,
        "id": user.id.hex,
        "favorites": [id_.hex for id_ in user.favorites],
        "name": user.name,
        "about": user.about,
        "updated_at": user.updated_at
    }


def assert_collection_find_called_with_correct_args(
        call_args: tuple,
        expected_search: SearchQuery,
        expected_sort: SortQuery,
        expected_limit: int,
        expected_projection: ProjectionQuery,
) -> None:
    args, kwargs = call_args
    actual_search, *_ = args
    actual_sort, actual_limit, actual_projection = operator.itemgetter("sort", "limit", "projection")(kwargs)

    assert expected_search == actual_search
    assert expected_sort == actual_sort
    assert expected_limit == actual_limit
    assert expected_projection == actual_projection


@pytest.mark.mongo_repo
@pytest.mark.user
class TestMongoUsersRepositoryFilterMethod:
    async def test_empty_iterator(
            self,
            mocker: MockFixture,
            user_storage_and_collection: StorageAndCollection,
            mock_motor_cursor_factory: Callable,
    ) -> None:
        """Basically mocks demo."""

        mongodb_storage, mock_collection = user_storage_and_collection
        cursor = mock_motor_cursor_factory([])
        mock_collection.find = mocker.Mock(return_value=cursor)

        repository = await UsersRepository(mongodb_storage)
        collected_items = [item async for item in repository.filter()]
        assert collected_items == []

    async def test_filter_by_time_only(
            self,
            mocker: MockFixture,
            user_storage_and_collection: StorageAndCollection,
            user_entity_factory: UserEntityProtocol,
            mock_motor_cursor_factory: Callable,
    ) -> None:
        start_time = datetime.now(tz=timezone.utc)
        mid_time = start_time + timedelta(seconds=5)
        end_time = start_time + timedelta(seconds=10)
        user_1 = user_entity_factory(alias="user_1", updated_at=start_time)
        user_2 = user_entity_factory(alias="user_2", updated_at=mid_time)
        user_3 = user_entity_factory(alias="user_3", updated_at=end_time)
        expected_users = [user_1, user_2, user_3]

        mongodb_storage, mock_collection = user_storage_and_collection
        cursor = mock_motor_cursor_factory([user_entity_to_dict(user) for user in expected_users])
        mock_collection.find = mocker.Mock(return_value=cursor)

        expected_search_query: SearchQuery = {
            "updated_at": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        expected_sort_query: SortQuery = [("updated_at", ASCENDING)]
        expected_limit = 0
        expected_projection_query: ProjectionQuery = None

        repository = await UsersRepository(mongodb_storage)
        actual_users = [item async for item in repository.filter(updated_after=start_time, updated_before=end_time)]

        assert len(expected_users) == len(actual_users)
        for expected_user, actual_user in zip(expected_users, actual_users):
            assert expected_user.alias == actual_user.alias
            assert expected_user.updated_at == actual_user.updated_at
            assert start_time <= actual_user.updated_at <= end_time

        mock_collection.find.assert_called_once()
        assert_collection_find_called_with_correct_args(
            mock_collection.find.call_args,
            expected_search_query,
            expected_sort_query,
            expected_limit,
            expected_projection_query,
        )
