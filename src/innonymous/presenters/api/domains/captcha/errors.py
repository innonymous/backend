from innonymous.presenters.api.errors import APIError

__all__ = ("CaptchaError", "CaptchaInvalidError")


class CaptchaError(APIError):
    pass


class CaptchaInvalidError(CaptchaError):
    __message__ = "Captcha is invalid."
