from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import UUID

import msgpack
from aio_pika import IncomingMessage, Message
from pydantic import parse_obj_as

from innonymous.data.storages.rabbitmq import RabbitMQStorage
from innonymous.domains.events.entities import EventEntity
from innonymous.domains.events.errors import EventsDeserializingError, EventsError, EventsSerializingError

__all__ = ("EventsRepository",)


class EventsRepository:
    def __init__(self, storage: RabbitMQStorage) -> None:
        self.__storage = storage

    async def publish(self, entity: EventEntity) -> None:
        serialized = self.__serialize(entity)

        try:
            await self.__storage.exchange.publish(Message(serialized), routing_key="")

        except Exception as exception:
            message = f"Cannot publish event: {exception}"
            raise EventsError(message) from exception

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[AsyncIterator[EventEntity]]:
        try:
            channel = await self.__storage.connection.channel()

        except Exception as exception:
            message = f"Cannot subscribe to events: {exception}"
            raise EventsError(message) from exception

        try:
            queue = await channel.declare_queue(exclusive=True, auto_delete=True)
            await queue.bind(self.__storage.exchange)

            async with queue.iterator(no_ack=True) as stream:
                yield self.__iterator(stream)  # type: ignore[arg-type]

        except Exception as exception:
            message = f"Cannot subscribe to events: {exception}"
            raise EventsError(message) from exception

        finally:
            await channel.close()

    async def shutdown(self) -> None:
        await self.__storage.shutdown()

    @staticmethod
    def __serialize(entity: EventEntity) -> bytes:
        def _pack(obj: Any) -> Any:
            if isinstance(obj, UUID):
                return obj.hex

            if isinstance(obj, datetime):
                return obj.isoformat()

            if is_dataclass(obj):
                return asdict(obj)

            message = f"Cannot encode: {obj}."
            raise TypeError(message)

        try:
            return msgpack.packb(entity, default=_pack)

        except Exception as exception:
            raise EventsSerializingError(entity=entity) from exception

    @staticmethod
    def __deserialize(entity: bytes) -> EventEntity:
        try:
            return parse_obj_as(EventEntity, msgpack.unpackb(entity, strict_map_key=False))  # type: ignore[arg-type]

        except Exception as exception:
            raise EventsDeserializingError(entity=entity) from exception

    @classmethod
    async def __iterator(cls, stream: AsyncIterator[IncomingMessage]) -> AsyncIterator[EventEntity]:
        try:
            async for entity in stream:
                yield cls.__deserialize(entity.body)

        except EventsDeserializingError as exception:
            raise exception

        except Exception as exception:
            message = f"Cannot receive events: {exception}"
            raise EventsError(message) from exception
