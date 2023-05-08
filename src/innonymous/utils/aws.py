from asyncio import Queue
from typing import Any

from aioboto3 import Session
from aiobotocore.client import AioBaseClient

__all__ = ("AWSClient", "AWSSession")


class AWSClient:
    def __init__(self, session: "AWSSession") -> None:
        self.__session = session
        self.__client = None

    async def __aenter__(self) -> Any:
        if self.__client is not None:
            message = "Client is already in use."
            raise ValueError(message)

        # Get client from the pool.
        self.__client = await self.__session._get_client()
        return self.__client

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.__client is None:
            message = "Client is already released."
            raise ValueError(message)

        # Make sure, that next call of __aexit__ is impossible.
        client = self.__client
        self.__client = None

        # Return client to the pool.
        await self.__session._return_client(client)


class AWSSession:
    def __init__(self, resource: str, *, max_saved_connections: int = 128, region: str | None = None) -> None:
        self.__resource = resource
        self.__session = Session(region_name=region)
        self.__pool: Queue[AioBaseClient] = Queue(maxsize=max_saved_connections)
        self.__active_clients: set[AioBaseClient] = set()
        self.__is_closed = False

    def get_client(self) -> AWSClient:
        return AWSClient(self)

    async def shutdown(self) -> None:
        if self.__is_closed:
            return

        self.__is_closed = True

        # Remove active clients.
        for client in self.__active_clients:
            await client.__aexit__(None, None, None)

    async def _get_client(self) -> AioBaseClient:
        if self.__is_closed:
            message = "Session is closed."
            raise RuntimeError(message)

        # If we have an available client.
        if not self.__pool.empty():
            return self.__pool.get_nowait()

        # If we do not have available client then create new.
        client = await self.__session.client(self.__resource).__aenter__()
        # Track opened connections.
        self.__active_clients.add(client)

        return client

    async def _return_client(self, client: AioBaseClient) -> None:
        if self.__is_closed:
            message = "Session is closed."
            raise RuntimeError(message)

        # Save client if we have space.
        if not self.__pool.full():
            self.__pool.put_nowait(client)
            return

        # We cannot save the client, destroy.
        await client.__aexit__(None, None, None)
        # Track opened connections.
        self.__active_clients.remove(client)

    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        await self.shutdown()
