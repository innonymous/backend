from innonymous.errors import InnonymousError

__all__ = ("APIError", "APIUnauthorizedError")


class APIError(InnonymousError):
    pass


class APIUnauthorizedError(APIError):
    __message__ = "Token is invalid or expired, or user not found."
