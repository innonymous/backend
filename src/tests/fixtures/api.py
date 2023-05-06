import os

import pytest
from httpx import AsyncClient

__all__ = ("api_client",)


@pytest.fixture()
async def api_client() -> AsyncClient:
    os.environ["INNONYMOUS_JWT_KEY"] = "test"

    from innonymous.presenters.api.application import application

    async with AsyncClient(app=application, base_url="http://test") as client:
        yield client
