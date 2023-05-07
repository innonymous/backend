from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pytest_mock import MockFixture
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from innonymous.data.repositories.users import UsersRepository
from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.users.entities import UserEntity
from innonymous.domains.users.errors import UsersAlreadyExistsError

from tests.conftest import UserEntityProtocol

__all__ = ()

StorageAndCollection = tuple[MongoDBStorage, AsyncIOMotorCollection]


@pytest.fixture
async def storage_and_collection(
        mocker: MockFixture, mock_mongodb_storage: MongoDBStorage, mock_mongodb_collection: AsyncIOMotorCollection
) -> StorageAndCollection:
    mock_mongodb_storage.client = mocker.MagicMock(spec=AsyncIOMotorDatabase)
    mock_mongodb_storage.client.__getitem__ = mocker.Mock(return_value=mock_mongodb_collection)

    return mock_mongodb_storage, mock_mongodb_collection


def assert_successful_create_with_right_args(call_args: tuple, expected_user: UserEntity) -> None:
    args, _ = call_args
    user_fields, *_ = args

    assert user_fields["salt"] == expected_user.salt
    assert user_fields["payload"] == expected_user.payload
    assert user_fields["alias"] == expected_user.alias

    assert user_fields["id"] == expected_user.id.hex
    assert user_fields["name"] == expected_user.name
    assert user_fields["about"] == expected_user.about
    assert user_fields["updated_at"] == expected_user.updated_at

    assert all(actual == expected.hex for actual, expected in zip(user_fields["favorites"], expected_user.favorites))


@pytest.mark.mongo_repo
class TestMongoDbUsersRepository:
    async def test_successful_create(
            self, mocker: MockFixture, storage_and_collection: StorageAndCollection,
            user_entity_factory: UserEntityProtocol
    ) -> None:
        mongodb_storage, mock_collection = storage_and_collection
        mock_collection.insert_one = mocker.AsyncMock()

        current_time = datetime.now(tz=timezone.utc)
        user = user_entity_factory(
            salt="salt",
            payload="payload",
            alias="alias",
            id=uuid4(),
            favorites=[uuid4() for i in range(5)],
            name="name",
            about="about",
            updated_at=current_time,
        )

        repository = await UsersRepository(mongodb_storage)
        await repository.create(user)

        mock_collection.insert_one.assert_awaited_once()
        assert_successful_create_with_right_args(mock_collection.insert_one.call_args, user)

    async def test_create_duplicate_user(
            self, mocker: MockFixture, storage_and_collection: StorageAndCollection,
            user_entity_factory: UserEntityProtocol
    ) -> None:
        mongodb_storage, mock_collection = storage_and_collection
        mock_collection.insert_one = mocker.AsyncMock(side_effect=DuplicateKeyError("E X I S T"))

        current_time = datetime.now(tz=timezone.utc)
        duplicate_user = user_entity_factory(
            salt="other salt",
            payload="other payload",
            alias="existing_alias",
            id=uuid4(),
            updated_at=current_time,
        )

        repository = await UsersRepository(mongodb_storage)

        with pytest.raises(UsersAlreadyExistsError):
            await repository.create(duplicate_user)

        mock_collection.insert_one.assert_awaited_once()
        assert_successful_create_with_right_args(mock_collection.insert_one.call_args, duplicate_user)
