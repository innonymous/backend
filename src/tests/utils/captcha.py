import hmac
import itertools

import orjson
import pybase64

from innonymous.presenters.api.domains.captcha.interactors import CaptchaInteractor

__all__ = ("solve_captcha",)


def solve_captcha(key: bytes, token: str) -> str:
    # Middle part of jwt token.
    body = token.split(".")[1]
    # Decode base64 token. Fix padding, since JWT does not use it.
    data = pybase64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    # Get hash from token.
    expected_hash = bytes.fromhex(orjson.loads(data)["hash"])

    for candidate in itertools.product(CaptchaInteractor.ALPHABET, repeat=CaptchaInteractor.LENGTH):
        secret = "".join(candidate)
        if hmac.digest(key, secret.encode(), CaptchaInteractor.ALGORITHM) == expected_hash:
            return secret

    message = "Cannot solve the captcha."
    raise ValueError(message)
