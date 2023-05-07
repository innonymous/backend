from starlette.datastructures import Headers
from starlette.middleware.gzip import GZipMiddleware as _GZipMiddleware, GZipResponder
from starlette.types import ASGIApp, Receive, Scope, Send

__all__ = ("GZipMiddleware",)


class GZipMiddleware(_GZipMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.__get_responder(scope)(scope, receive, send)

    def __get_responder(self, scope: Scope) -> GZipResponder | ASGIApp:
        if scope["type"] != "http":
            return self.app

        # Get headers.
        headers = Headers(scope=scope)

        # Do not need to use gzip on event stream or when no content encoding header.
        if "text/event-stream" in headers.get("Accept", "") or "gzip" not in headers.get("Accept-Encoding", ""):
            return self.app

        return GZipResponder(self.app, self.minimum_size, compresslevel=self.compresslevel)
