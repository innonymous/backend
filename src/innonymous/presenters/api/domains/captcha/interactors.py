import hmac
import random
import string

from innonymous.presenters.api.data.repositories.captcha import CaptchaRepository
from innonymous.presenters.api.domains.captcha.entities import CaptchaEntity, CaptchaSolvedEntity
from innonymous.presenters.api.domains.captcha.errors import CaptchaError, CaptchaInvalidError
from innonymous.presenters.api.domains.tokens.entities import TokenCaptchaEntity
from innonymous.presenters.api.domains.tokens.interactors import TokensInteractor

__all__ = ("CaptchaInteractor",)


class CaptchaInteractor:
    LENGTH = 4
    ALGORITHM = "SHA256"
    # Use a-z, 0-9, except similar characters.
    ALPHABET = "".join(set(string.ascii_lowercase + string.digits).difference(set("9q0ocda17uv6bil2z5s")))

    def __init__(self, key: bytes, captcha_repository: CaptchaRepository, tokens_interactor: TokensInteractor) -> None:
        self.__key = key
        self.__captcha_repository = captcha_repository
        self.__tokens_interactor = tokens_interactor

    def verify(self, entity: CaptchaSolvedEntity) -> None:
        try:
            token: TokenCaptchaEntity = self.__tokens_interactor.decode(
                entity.token, audience="captcha"
            )  # type: ignore[assignment]

            hash_ = self.__get_hash(entity.secret)

        except Exception as exception:
            raise CaptchaInvalidError() from exception

        if token.hash != hash_:
            raise CaptchaInvalidError()

    async def create(self) -> CaptchaEntity:
        secret = "".join(random.choices(self.ALPHABET, k=self.LENGTH))  # noqa: S311

        return CaptchaEntity(
            image=await self.__captcha_repository.generate(secret),
            token=self.__tokens_interactor.encode(
                TokenCaptchaEntity(hash=self.__get_hash(secret))
            ),  # type: ignore[assignment]
        )

    def __get_hash(self, secret: str) -> bytes:
        try:
            return hmac.digest(self.__key, secret.encode(), self.ALGORITHM)

        except Exception as exception:
            message = f"Cannot get hash of secret: {exception}"
            raise CaptchaError(message) from exception
