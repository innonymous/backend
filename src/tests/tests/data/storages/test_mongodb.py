import pytest

from innonymous.data.storages.mongodb import MongoDBStorage


__all__ = ("test_mongodb",)


@pytest.mark.it("Simple mongodb storage check.")
async def test_mongodb(mongodb_storage: MongoDBStorage) -> None:
    await mongodb_storage.client.list_collection_names()
