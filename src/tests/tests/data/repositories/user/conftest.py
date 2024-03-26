import pytest
from pytest_mock import MockFixture
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from innonymous.data.storages.mongodb import MongoDBStorage

StorageAndCollection = tuple[MongoDBStorage, AsyncIOMotorCollection]


@pytest.fixture
async def user_storage_and_collection(
    mocker: MockFixture, mock_mongodb_storage: MongoDBStorage, mock_mongodb_collection: AsyncIOMotorCollection
) -> StorageAndCollection:
    mock_mongodb_storage.client = mocker.MagicMock(spec=AsyncIOMotorDatabase)
    mock_mongodb_storage.client.__getitem__ = mocker.Mock(return_value=mock_mongodb_collection)

    return mock_mongodb_storage, mock_mongodb_collection
