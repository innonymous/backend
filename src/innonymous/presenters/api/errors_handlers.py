from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError

from innonymous.domains.sessions.errors import SessionsNotFoundError
from innonymous.domains.users.errors import UsersNotFoundError
from innonymous.presenters.api.application import application
from innonymous.presenters.api.domains.captcha.errors import CaptchaInvalidError
from innonymous.presenters.api.errors import APIUnauthorizedError

__all__ = ("not_found", "bad_request", "unauthorized", "unprocessable_entity")


@application.exception_handler(UsersNotFoundError)  # type: ignore[has-type]
@application.exception_handler(SessionsNotFoundError)  # type: ignore[has-type]
async def not_found(_: Request, exception: UsersNotFoundError | SessionsNotFoundError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_404_NOT_FOUND)


@application.exception_handler(CaptchaInvalidError)  # type: ignore[has-type]
async def bad_request(_: Request, exception: CaptchaInvalidError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_400_BAD_REQUEST)


@application.exception_handler(APIUnauthorizedError)  # type: ignore[has-type]
async def unauthorized(_: Request, exception: APIUnauthorizedError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_401_UNAUTHORIZED)


@application.exception_handler(ValidationError)  # type: ignore[has-type]
@application.exception_handler(RequestValidationError)  # type: ignore[has-type]
async def unprocessable_entity(_: Request, exception: ValidationError | RequestValidationError) -> ORJSONResponse:
    return ORJSONResponse(
        content={"alias": "ValidationError", "attributes": {"errors": exception.errors()}},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
