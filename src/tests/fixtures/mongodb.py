import asyncio
import os
from logging import getLogger
from typing import AsyncIterator, Callable
from uuid import uuid4

import pytest
from docker import DockerClient
from docker.models.containers import Container
from innonymous.data.storages.mongodb import MongoDBStorage


__all__ = ("mongodb_url", "mongodb_container", "mongodb_storage")


@pytest.fixture()
async def mongodb_url(mongodb_container: Container | None) -> AsyncIterator[str]:
    if mongodb_container is not None:
        url = f"mongodb://innonymous:innonymous@localhost:{list(mongodb_container.ports.values())[0]}"

    elif "INNONYMOUS_TEST_MONGODB_URL" in os.environ:
        url = os.environ["INNONYMOUS_TEST_MONGODB_URL"]
        getLogger().info(f"Using external MongoDB: {url}")

    else:
        raise RuntimeError("MongoDB is not available.")

    storage = await MongoDBStorage(url)

    for attempt in range(10):
        try:
            await storage.client.list_collection_names()
            break

        except Exception as exception:
            await asyncio.sleep(1)

            # Healthcheck failed.
            if attempt == 9:
                message = f"MongoDB healthcheck failed: {exception}"
                raise Exception(message) from exception

            continue

    yield url

    # Drop configured database.
    await storage.client.client.drop_database(storage.client.name)
    # Close.
    await storage.shutdown()


@pytest.fixture(scope="session")
def mongodb_container(
    docker_client: DockerClient | None, unused_tcp_port_factory: Callable[[], int]
) -> AsyncIterator[Container]:
    if docker_client is None:
        getLogger().error("Cannot create MongoDB, since docker is not available.")
        yield None
        return

    mongodb_port = unused_tcp_port_factory()
    mongodb: Container = docker_client.containers.run(
        image="mongo:6",
        name=f"innonymous-tests.mongodb.{uuid4()}",
        stdout=False,
        detach=True,
        remove=True,
        ports={"27017": mongodb_port},
        environment={"MONGO_INITDB_ROOT_USERNAME": "innonymous", "MONGO_INITDB_ROOT_PASSWORD": "innonymous"},
    )

    # Indicate, that we open port.
    mongodb.ports["27017"] = mongodb_port

    yield mongodb

    # Clear resources.
    mongodb.remove(v=True, force=True)


@pytest.fixture()
async def mongodb_storage(mongodb_url: str) -> AsyncIterator[MongoDBStorage]:
    storage = await MongoDBStorage(mongodb_url)
    yield storage
    await storage.shutdown()
