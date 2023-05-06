import asyncio
import os
from logging import getLogger
from typing import AsyncIterator, Callable
from uuid import uuid4

import pytest
from aiohttp import ClientSession
from docker import DockerClient
from docker.models.containers import Container

from innonymous.data.storages.rabbitmq import RabbitMQStorage

__all__ = ("rabbitmq_url", "rabbitmq_url_admin", "rabbitmq_container", "rabbitmq_storage")


@pytest.fixture()
async def rabbitmq_url(rabbitmq_container: Container | None, rabbitmq_url_admin: str) -> AsyncIterator[str]:
    if rabbitmq_container is not None:
        url = f"amqp://innonymous:innonymous@localhost:{list(rabbitmq_container.ports.values())[0]}"

    elif "INNONYMOUS_TEST_RABBITMQ_URL" in os.environ:
        url = os.environ["INNONYMOUS_TEST_RABBITMQ_URL"]
        getLogger().info(f"Using external RabbitMQ: {url}")

    else:
        raise RuntimeError("RabbitMQ is not available.")

    for attempt in range(10):
        try:
            async with ClientSession() as session, session.get(f"{rabbitmq_url_admin}/aliveness-test/%2F") as response:
                assert response.status < 300, f"Rabbit healthcheck failed: {await response.content.read()}"
                break

        except Exception as exception:
            await asyncio.sleep(1)

            # Healthcheck failed.
            if attempt == 9:
                message = f"Rabbit healthcheck failed: {exception}"
                raise Exception(message) from exception

            continue

    yield url

    # Delete all queues and exchanges.
    async with ClientSession() as session:
        for objects in ("queues", "exchanges"):
            async with session.get(f"{rabbitmq_url_admin}/{objects}/%2F/") as response:
                body = await response.json()
                assert response.status < 300, f"Invalid response {response.status}: {body}"

            for obj in body:
                # Delete exchanges that we created.
                if "user_who_performed_action" in obj and obj["user_who_performed_action"] != "innonymous":
                    continue

                # We cannot delete exclusive queues.
                if obj.get("exclusive"):
                    continue

                async with session.delete(f"{rabbitmq_url_admin}/{objects}/%2F/{obj['name']}") as response:
                    assert response.status < 300, f"Invalid response {response.status}: {await response.content.read()}"


@pytest.fixture(scope="session")
def rabbitmq_url_admin(rabbitmq_container: Container | None) -> str:
    if rabbitmq_container is not None:
        return f"http://innonymous:innonymous@localhost:{list(rabbitmq_container.ports.values())[1]}/api"

    if "INNONYMOUS_TEST_RABBITMQ_URL_ADMIN" in os.environ:
        url = f"{os.environ['INNONYMOUS_TEST_RABBITMQ_URL_ADMIN']}/api"
        getLogger().info(f"Using external RabbitMQ Admin: {url}")
        return url

    raise RuntimeError("RabbitMQ is not available.")


@pytest.fixture(scope="session")
def rabbitmq_container(
    docker_client: DockerClient | None, unused_tcp_port_factory: Callable[[], int]
) -> AsyncIterator[Container | None]:
    if docker_client is None:
        getLogger().info("Cannot create RabbitMQ, since docker is not available.")
        yield None
        return

    amqp_port = unused_tcp_port_factory()
    admin_port = unused_tcp_port_factory()

    rabbitmq: Container = docker_client.containers.run(
        image="rabbitmq:3.10-management-alpine",
        name=f"innonymous-tests.rabbitmq.{uuid4()}",
        stdout=False,
        detach=True,
        ports={"5672": amqp_port, "15672": admin_port},
        environment={"RABBITMQ_DEFAULT_USER": "innonymous", "RABBITMQ_DEFAULT_PASS": "innonymous"},
    )

    # Indicate, that we open port.
    rabbitmq.ports["5672"] = amqp_port
    rabbitmq.ports["15672"] = admin_port

    yield rabbitmq

    # Clear resources.
    rabbitmq.remove(v=True, force=True)


@pytest.fixture()
async def rabbitmq_storage(rabbitmq_url: str, rabbitmq_url_admin: str) -> AsyncIterator[RabbitMQStorage]:
    storage = await RabbitMQStorage(rabbitmq_url)
    yield storage
    await storage.shutdown()
