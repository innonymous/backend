import pytest
from aiohttp import ClientSession

from innonymous.data.storages.rabbitmq import RabbitMQStorage

__all__ = ("test_rabbitmq",)


@pytest.mark.skip(reason="may be unnecessary or not viable")
async def test_rabbitmq(rabbitmq_storage: RabbitMQStorage, rabbitmq_url_admin: str) -> None:
    async with ClientSession().get(f"{rabbitmq_url_admin}/exchanges/%2F/{rabbitmq_storage.exchange.name}") as response:
        body = await response.json()
        assert response.status < 300, f"Invalid response {response.status}: {body}"

    # Check that exchange created.
    assert body["durable"], "Exchange should be durable."
    assert body["type"] == "fanout", "Exchange should be with fanout type."
