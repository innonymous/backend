from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from innonymous.presenters.innonymous import Innonymous

__all__ = ("innonymous",)

application = FastAPI(
    title="Innonymous API",
    version="2.0.0",
    default_response_class=ORJSONResponse,
    contact={"name": "Ivan Izmailov", "url": "https://t.me/smthngslv", "email": "smthngslv@optic.xyz"},
)

# Allow CORS.
application.add_middleware(
    CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
# Allow gzip.
application.add_middleware(GZipMiddleware)

# Main presenter.
innonymous = Innonymous()


@application.on_event("startup")
async def on_startup() -> None:
    await innonymous


@application.on_event("shutdown")
async def on_shutdown() -> None:
    await innonymous.shutdown()


# Include views.
from innonymous.presenters.api.endpoints import router  # noqa: E402

application.include_router(router, prefix="/v2")  # type: ignore[has-type]
