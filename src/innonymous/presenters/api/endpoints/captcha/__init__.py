from fastapi import APIRouter

router = APIRouter(tags=["captcha"], prefix="/captcha")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.captcha.views  # noqa: F401, E402
