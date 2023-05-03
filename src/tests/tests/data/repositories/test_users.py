import pytest

from innonymous.data.repositories.users import UsersRepository
from innonymous.data.storages.mongodb import MongoDBStorage


@pytest.mark.it("Repository mocked testing.")
async def test_repository_mocked(mongodb_storage: "MockedMongoDBStorage") -> None:
    repository = await UsersRepository(mongodb_storage)
    await repository.shutdown()


@pytest.mark.it("Repository testing.")
async def test_repository(mongodb_storage: MongoDBStorage) -> None:
    repository = await UsersRepository(mongodb_storage)
    await repository.shutdown()
