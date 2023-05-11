from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError

from innonymous.domains.chats.errors import ChatsAlreadyExistsError, ChatsNotFoundError
from innonymous.domains.messages.errors import MessagesNotFoundError, MessagesUpdateError
from innonymous.domains.sessions.errors import SessionsNotFoundError
from innonymous.domains.users.errors import UsersAlreadyExistsError, UsersInvalidCredentialsError, UsersNotFoundError
from innonymous.presenters.api.application import application
from innonymous.presenters.api.domains.captcha.errors import CaptchaInvalidError
from innonymous.presenters.api.errors import APIUnauthorizedError

__all__ = ("not_found", "bad_request", "unauthorized", "unprocessable_entity")


@application.exception_handler(UsersNotFoundError)  # type: ignore[has-type]
@application.exception_handler(ChatsNotFoundError)  # type: ignore[has-type]
@application.exception_handler(SessionsNotFoundError)  # type: ignore[has-type]
@application.exception_handler(MessagesNotFoundError)  # type: ignore[has-type]
async def not_found(
    _: Request, exception: UsersNotFoundError | SessionsNotFoundError | ChatsNotFoundError | MessagesNotFoundError
) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_404_NOT_FOUND)


@application.exception_handler(CaptchaInvalidError)  # type: ignore[has-type]
async def bad_request(_: Request, exception: CaptchaInvalidError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_400_BAD_REQUEST)


@application.exception_handler(UsersAlreadyExistsError)  # type: ignore[has-type]
@application.exception_handler(ChatsAlreadyExistsError)  # type: ignore[has-type]
async def conflict(_: Request, exception: UsersAlreadyExistsError | ChatsAlreadyExistsError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_409_CONFLICT)


@application.exception_handler(APIUnauthorizedError)  # type: ignore[has-type]
@application.exception_handler(UsersInvalidCredentialsError)  # type: ignore[has-type]
async def unauthorized(_: Request, exception: APIUnauthorizedError | UsersInvalidCredentialsError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_401_UNAUTHORIZED)


@application.exception_handler(ValidationError)  # type: ignore[has-type]
@application.exception_handler(RequestValidationError)  # type: ignore[has-type]
async def unprocessable_entity(_: Request, exception: ValidationError | RequestValidationError) -> ORJSONResponse:
    return ORJSONResponse(
        content={"alias": "ValidationError", "attributes": {"errors": exception.errors()}},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@application.exception_handler(MessagesUpdateError)  # type: ignore[has-type]
async def forbidden(_: Request, exception: MessagesUpdateError) -> ORJSONResponse:
    return ORJSONResponse(content=exception.to_dict(include_traceback=False), status_code=status.HTTP_403_FORBIDDEN)
