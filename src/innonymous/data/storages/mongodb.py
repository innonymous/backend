from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from innonymous.utils import AsyncLazyObject

__all__ = ("MongoDBStorage",)


class MongoDBStorage(AsyncLazyObject):
    async def __ainit__(self, mongo_url: str, *, db: str = "innonymous") -> None:
        self.__client = AsyncIOMotorClient(mongo_url)[db]

    @property
    def client(self) -> AsyncIOMotorDatabase:
        return self.__client

    async def shutdown(self) -> None:
        self.__client.client.close()
