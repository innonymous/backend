import pytest
from pytest_mock import MockFixture
from motor.motor_asyncio import AsyncIOMotorCollection

from innonymous.data.storages.mongodb import MongoDBStorage

__all__ = ()


@pytest.fixture
async def mock_mongodb_storage(mocker: MockFixture) -> MongoDBStorage:
    return mocker.Mock(spec=MongoDBStorage)


@pytest.fixture
async def mock_mongodb_collection(mocker: MockFixture) -> AsyncIOMotorCollection:
    mock_collection = mocker.AsyncMock(spec=AsyncIOMotorCollection)
    mock_collection.create_indexes = mocker.AsyncMock()
    return mock_collection
