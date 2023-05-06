from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from innonymous.presenters.api.data.repositories.captcha import CaptchaRepository
from innonymous.presenters.api.data.repositories.tokens import TokensRepository
from innonymous.presenters.api.domains.captcha.interactors import CaptchaInteractor
from innonymous.presenters.api.domains.tokens.interactors import TokensInteractor
from innonymous.presenters.innonymous import Innonymous

__all__ = ("innonymous", "tokens_interactor", "captcha_interactor")

from innonymous.settings import Settings

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

settings = Settings()
# Main presenter.
innonymous = Innonymous(settings=settings)

if settings.JWT_KEY is None:
    message = "You should provide jwt key."
    raise Exception(message)

# This will be used for authentication anc captcha.
tokens_interactor = TokensInteractor(TokensRepository(settings.JWT_KEY))
# This will be used to avoid spamming.
captcha_interactor = CaptchaInteractor(settings.JWT_KEY.encode(), CaptchaRepository(), tokens_interactor)


@application.on_event("startup")
async def on_startup() -> None:
    await innonymous


@application.on_event("shutdown")
async def on_shutdown() -> None:
    await innonymous.shutdown()


# Include views.
from innonymous.presenters.api.endpoints import router  # noqa: E402

application.include_router(router, prefix="/v2")  # type: ignore[has-type]
