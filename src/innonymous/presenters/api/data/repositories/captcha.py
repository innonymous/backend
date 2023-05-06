from asyncio import get_running_loop

from captcha.image import ImageCaptcha

from innonymous.presenters.api.domains.captcha.errors import CaptchaError

__all__ = ("CaptchaRepository",)


class CaptchaRepository:
    def __init__(self) -> None:
        self.__captcha = ImageCaptcha()

    async def generate(self, secret: str) -> bytes:
        try:
            # Run in thread to avoid any blocking.
            with await get_running_loop().run_in_executor(None, self.__captcha.generate, secret, "jpeg") as buffer:
                return buffer.getvalue()

        except Exception as exception:
            message = f"Cannot generate captcha: {exception}"
            raise CaptchaError(message) from exception
