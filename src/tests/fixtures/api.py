import os

import pytest
from httpx import AsyncClient

__all__ = ("api_client",)


@pytest.fixture()
async def api_client(mongodb_url: str, rabbitmq_url: str) -> AsyncClient:
    os.environ["INNONYMOUS_JWT_KEY"] = "test"
    os.environ["INNONYMOUS_DATABASE_URL"] = mongodb_url
    os.environ["INNONYMOUS_BROKER_URL"] = rabbitmq_url

    from innonymous.presenters.api.application import application

    async with AsyncClient(app=application, base_url="http://test") as client:
        yield client


@pytest.fixture()
async def api_client_mocked() -> AsyncClient:
    os.environ["INNONYMOUS_JWT_KEY"] = "test"

    # TODO: Mock MongoDBStorage
    # TODO: Mock RabbitMQStorage
    from innonymous.presenters.api.application import application

    async with AsyncClient(app=application, base_url="http://test") as client:
        yield client
