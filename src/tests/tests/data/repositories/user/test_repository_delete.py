from typing import Any
from uuid import uuid4

import pytest
from pytest_mock import MockFixture
from pymongo.results import DeleteResult

from innonymous.data.repositories.users import UsersRepository

from tests.conftest import UserEntityProtocol
from tests.tests.data.repositories.user.conftest import StorageAndCollection

__all__ = ()


def assert_delete_one_with_correct_query(call_args: tuple, expected_query: dict[str, Any]) -> None:
    args, _ = call_args
    actual_query, *_ = args

    assert expected_query == actual_query


@pytest.mark.mongo_repo
@pytest.mark.user
class TestMongoUsersRepositoryDeleteMethod:
    @pytest.mark.parametrize("expected_is_deleted,deleted_count", [(True, 1), (False, 0)])
    async def test_successful_delete(
        self,
        mocker: MockFixture,
        user_storage_and_collection: StorageAndCollection,
        expected_is_deleted: bool,
        deleted_count: int,
    ) -> None:
        mongodb_storage, mock_collection = user_storage_and_collection

        delete_result = mocker.MagicMock(spec=DeleteResult)
        type(delete_result).deleted_count = mocker.PropertyMock(return_value=deleted_count)

        mock_collection.delete_one = mocker.AsyncMock(return_value=delete_result)

        some_valid_id = uuid4()
        expected_query = {"id": some_valid_id.hex}

        repository = await UsersRepository(mongodb_storage)
        is_deleted_successfully = await repository.delete(id_=some_valid_id)

        assert expected_is_deleted == is_deleted_successfully
        mock_collection.delete_one.assert_awaited_once()
        assert_delete_one_with_correct_query(mock_collection.delete_one.call_args, expected_query)
