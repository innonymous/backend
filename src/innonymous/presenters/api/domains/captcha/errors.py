from innonymous.errors import InnonymousError

__all__ = ("CaptchaError", "CaptchaInvalidError")


class CaptchaError(InnonymousError):
    pass


class CaptchaInvalidError(InnonymousError):
    __message__ = "Captcha is invalid."
