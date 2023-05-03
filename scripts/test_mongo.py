import asyncio
import dataclasses
import os
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from innonymous.data.storages.mongodb import MongoDBStorage
from innonymous.domains.users.entities import UserEntity
from innonymous.settings import Settings

from pydantic.dataclasses import _validate_dataclass

async def main() -> None:
    settings = Settings()

    storage = await MongoDBStorage(settings.DATABASE_URL, db=settings.DATABASE_NAME)

    entity = UserEntity(
        alias="smthngslv",
        salt=os.urandom(16),
        payload=os.urandom(32),
    )

    dataclasses.replace(
        entity, updated=datetime.now(tz=timezone(timedelta(hours=2), "aa"))
    )

    serialized = asdict(entity)
    serialized["id"] = serialized["id"].hex

    print(serialized)

    # await storage.client["test"].insert_one(serialized)

    await storage.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
