from datetime import datetime, timezone, timedelta
from typing import Any, Callable
from uuid import uuid4

import pytest
from pytest_mock import MockFixture
from pymongo.results import UpdateResult
from pymongo.errors import DuplicateKeyError

from innonymous.data.repositories.users import UsersRepository
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import UsersAlreadyExistsError, UsersTransactionError, UsersNotFoundError

from tests.conftest import UserEntityProtocol
from tests.tests.data.repositories.user.conftest import StorageAndCollection

__all__ = ()


@pytest.fixture
def mock_update_result_factory(mocker: MockFixture) -> Callable:
    def factory(*, matched_count: int):
        update_result = mocker.MagicMock(spec=UpdateResult)
        type(update_result).matched_count = mocker.PropertyMock(return_value=matched_count)
        return update_result

    return factory


def user_entity_to_update_query(user: UserEntity) -> dict[str, dict[str, Any]]:
    return {
        "$set": {
            "salt": user.salt,
            "payload": user.payload,
            "alias": user.alias,
            "id": user.id.hex,
            "favorites": [id_.hex for id_ in user.favorites],
            "name": user.name,
            "about": user.about,
            "updated_at": user.updated_at,
        }
    }


def assert_update_one_with_correct_queries(
    call_args: tuple, search_query: dict[str, Any], update_query: dict[str, Any]
) -> None:
    args, _ = call_args
    actual_search_query, actual_update_query, *_ = args

    assert search_query == actual_search_query
    assert update_query == actual_update_query


@pytest.mark.mongo_repo
class TestMongoUsersRepositoryUpdateMethod:
    async def test_successful_update(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
        mock_update_result_factory: Callable,
    ) -> None:
        mongodb_storage, mock_collection = user_storage_and_collection

        update_result = mock_update_result_factory(matched_count=1)
        mock_collection.update_one = mocker.AsyncMock(return_value=update_result)

        unchanged_id = uuid4()
        last_updated_at = datetime.now(tz=timezone.utc)
        new_updated_at = last_updated_at + timedelta(seconds=5)
        user_to_store = user_entity_factory(
            salt="new salt",
            payload="new payload",
            alias="new_alias",
            id=unchanged_id,
            favorites=[uuid4() for _ in range(5)],
            name="new name",
            about="new description",
            updated_at=new_updated_at,
        )
        expected_search_query = {"id": user_to_store.id.hex, "updated_at": last_updated_at}
        expected_update_query = user_entity_to_update_query(user_to_store)

        repository = await UsersRepository(mongodb_storage)
        await repository.update(user_to_store, updated_at=last_updated_at)

        mock_collection.update_one.assert_awaited_once()
        assert_update_one_with_correct_queries(
            mock_collection.update_one.call_args, expected_search_query, expected_update_query
        )

    async def test_update_fails_when_new_alias_is_taken(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
    ) -> None:
        mongodb_storage, mock_collection = user_storage_and_collection

        mock_collection.update_one = mocker.AsyncMock(side_effect=DuplicateKeyError("D U P E"))

        unchanged_id = uuid4()
        last_updated_at = datetime.now(tz=timezone.utc)
        new_updated_at = last_updated_at + timedelta(seconds=5)
        user_to_store = user_entity_factory(
            salt="new salt",
            payload="new payload",
            alias="DUPLICATE_alias",
            id=unchanged_id,
            favorites=[uuid4() for _ in range(5)],
            name="new name",
            about="new description",
            updated_at=new_updated_at,
        )
        expected_search_query = {"id": user_to_store.id.hex, "updated_at": last_updated_at}
        expected_update_query = user_entity_to_update_query(user_to_store)

        repository = await UsersRepository(mongodb_storage)
        with pytest.raises(UsersAlreadyExistsError):
            await repository.update(user_to_store, updated_at=last_updated_at)

        mock_collection.update_one.assert_awaited_once()
        assert_update_one_with_correct_queries(
            mock_collection.update_one.call_args, expected_search_query, expected_update_query
        )

    async def test_user_not_found_without_updated_at(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
        mock_update_result_factory: Callable,
    ) -> None:
        mongodb_storage, mock_collection = user_storage_and_collection

        update_result = mock_update_result_factory(matched_count=0)
        mock_collection.update_one = mocker.AsyncMock(return_value=update_result)

        unchanged_id = uuid4()
        user_to_store = user_entity_factory(
            salt="new salt",
            payload="new payload",
            alias="new_alias",
            id=unchanged_id,
            favorites=[uuid4() for _ in range(5)],
            name="new name",
            about="new description",
            updated_at=datetime.now(tz=timezone.utc),
        )
        expected_search_query = {"id": user_to_store.id.hex}
        expected_update_query = user_entity_to_update_query(user_to_store)

        repository = await UsersRepository(mongodb_storage)
        with pytest.raises(UsersNotFoundError):
            await repository.update(user_to_store)

        mock_collection.update_one.assert_awaited_once()
        assert_update_one_with_correct_queries(
            mock_collection.update_one.call_args, expected_search_query, expected_update_query
        )

    async def test_transaction_error_when_last_update_time_changed_unexpectedly(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        user_entity_factory: UserEntityProtocol,
        mock_update_result_factory: Callable,
    ) -> None:
        """Here we test what happens when asyncio decides to process
        the 2nd request before the 1st one,
        so the `updated_at` for the 1st one becomes invalid.
        """

        mongodb_storage, mock_collection = user_storage_and_collection

        update_result_on_success = mock_update_result_factory(matched_count=1)
        update_result_on_failure = mock_update_result_factory(matched_count=0)

        repository = await UsersRepository(mongodb_storage)

        user_id = uuid4()
        original_updated_at = datetime.now(tz=timezone.utc)
        first_requested_user = user_entity_factory(
            salt="new salt",
            payload="new payload",
            alias="new_alias",
            id=user_id,
            favorites=[uuid4() for _ in range(5)],
            name="new name",
            about="new description",
            updated_at=datetime.now(tz=timezone.utc),
        )
        second_requested_user = user_entity_factory(
            salt="newest salt",
            payload="newest payload",
            alias="newest_alias",
            id=user_id,
            favorites=[uuid4() for _ in range(5)],
            name="newest name",
            about="newest description",
            updated_at=datetime.now(tz=timezone.utc),
        )
        expected_search_query = {"id": user_id.hex, "updated_at": original_updated_at}
        expected_first_update_request = user_entity_to_update_query(first_requested_user)
        expected_second_update_request = user_entity_to_update_query(second_requested_user)

        mock_collection.update_one = mocker.AsyncMock(return_value=update_result_on_success)
        await repository.update(second_requested_user, updated_at=original_updated_at)
        mock_collection.update_one.assert_awaited_once()
        assert_update_one_with_correct_queries(
            mock_collection.update_one.call_args, expected_search_query, expected_second_update_request
        )

        mock_collection.update_one = mocker.AsyncMock(return_value=update_result_on_failure)
        with pytest.raises(UsersTransactionError):
            await repository.update(first_requested_user, updated_at=original_updated_at)

        mock_collection.update_one.assert_awaited_once()
        assert_update_one_with_correct_queries(
            mock_collection.update_one.call_args, expected_search_query, expected_first_update_request
        )
