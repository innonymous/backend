import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import urlsplit
from uuid import uuid4

from innonymous.utils.aws import AWSSession

__all__ = ("S3Session",)


class S3Session:
    def __init__(self, *, bucket: str | None = None, bucket_root: str | None = None) -> None:
        self.__bucket = bucket
        self.__bucket_root = Path(bucket_root if bucket_root is not None else ".")
        self.__session = AWSSession("s3")

    async def upload(
        self,
        file: bytes | BinaryIO,
        *,
        path: str | None = None,
        bucket: str | None = None,
        bucket_root: str | None = None,
        timeout: float | None = None,
    ) -> str:
        # Use random name if not provided.
        path = path if path is not None else uuid4().hex

        # Target key.
        bucket, key = self.__get_bucket_and_key(path, bucket=bucket, bucket_root=bucket_root)

        # Wrap into binary io if it is bytes.
        if isinstance(file, bytes):
            with BytesIO(file) as buffer:
                await self.__upload(bucket, key, buffer, timeout=timeout)

        else:
            await self.__upload(bucket, key, file, timeout=timeout)

        return f"s3://{bucket}/{key}"

    async def download(
        self,
        *,
        url: str | None = None,
        path: str | None = None,
        bucket: str | None = None,
        bucket_root: str | None = None,
        destination: BinaryIO | None = None,
        timeout: float | None = None,
    ) -> bytes | None:
        if url is not None:
            bucket, key = self.__parse_s3_url(url)

        elif path is not None:
            # Target key.
            bucket, key = self.__get_bucket_and_key(path, bucket=bucket, bucket_root=bucket_root)

        else:
            message = "You should specify url or path."
            raise ValueError(message)

        if destination is None:
            with BytesIO() as file:
                await self.__download(bucket, key, file, timeout=timeout)
                return file.getvalue()

        # Download to destination.
        await self.__download(bucket, key, destination, timeout=timeout)
        return None

    async def shutdown(self) -> None:
        await self.__session.shutdown()

    async def __upload(self, bucket: str, key: str, file: BinaryIO, *, timeout: float | None = None) -> None:
        async with self.__session.get_client() as client:
            try:
                await asyncio.wait_for(client.upload_fileobj(file, bucket, key), timeout=timeout)

            except asyncio.TimeoutError as exception:
                raise TimeoutError() from exception

    async def __download(
        self,
        bucket: str,
        key: str,
        file: BinaryIO,
        *,
        timeout: float | None = None,
    ) -> None:
        async with self.__session.get_client() as client:
            try:
                await asyncio.wait_for(client.download_fileobj(bucket, key, file), timeout=timeout)

            except asyncio.TimeoutError as exception:
                raise TimeoutError() from exception

    @staticmethod
    def __parse_s3_url(url: str) -> tuple[str, str]:
        _url = urlsplit(url, scheme="s3")

        if _url.scheme != "s3":
            message = f"Link {url} not valid S3 URL."
            raise ValueError(message)

        if not _url.netloc:
            message = f"Bucket is not provided: {url}"
            raise ValueError(message)

        # Parse path.
        path = Path(_url.path)
        if path.is_absolute():
            path = path.relative_to("/")

        # Path is not provided.
        if path.as_posix() == ".":
            message = f"Path is not provided: {url}"
            raise ValueError(message)

        return _url.netloc, path.as_posix()

    def __get_bucket_and_key(
        self, path: str, *, bucket: str | None = None, bucket_root: str | None = None
    ) -> tuple[str, str]:
        bucket = bucket if bucket is not None else self.__bucket
        if bucket is None:
            message = "You should specify bucket."
            raise ValueError(message)

        # Use "." if not provided.
        root = Path(bucket_root) if bucket_root is not None else self.__bucket_root

        # Target key.
        return bucket, (root / path).as_posix()

    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        await self.shutdown()
