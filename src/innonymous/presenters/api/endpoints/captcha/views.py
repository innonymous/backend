from innonymous.presenters.api.application import captcha_interactor
from innonymous.presenters.api.endpoints.captcha import router
from innonymous.presenters.api.endpoints.captcha.schemas import CaptchaSchema

__all__ = ("get",)


@router.get("", response_model=CaptchaSchema)
async def get() -> CaptchaSchema:
    return CaptchaSchema.from_entity(await captcha_interactor.create())
