from logging import getLogger

import docker
import pytest
from docker import DockerClient

__all__ = ("docker_client",)


@pytest.fixture(scope="session")
def docker_client() -> DockerClient | None:
    try:
        client = docker.from_env()
        client.ping()
        return client

    except Exception as exception:
        getLogger().exception(f"Cannot initialize docker: {exception}")
        return None
