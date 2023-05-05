import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractRobustExchange

from innonymous.utils import AsyncLazyObject

__all__ = ("RabbitMQStorage",)


class RabbitMQStorage(AsyncLazyObject):
    async def __ainit__(self, url: str, *, exchange: str = "events") -> None:
        self.__connection = await aio_pika.connect_robust(url)
        self.__channel = await self.__connection.channel()
        self.__exchange = await self.__channel.declare_exchange(exchange, ExchangeType.FANOUT, durable=True)

    @property
    def connection(self) -> AbstractRobustConnection:
        return self.__connection

    @property
    def channel(self) -> AbstractRobustChannel:
        return self.__channel  # type: ignore[return-value]

    @property
    def exchange(self) -> AbstractRobustExchange:
        return self.__exchange  # type: ignore[return-value]

    async def shutdown(self) -> None:
        await self.__connection.close()
