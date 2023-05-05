from fastapi import APIRouter

router = APIRouter(tags=["system"], prefix="/system")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.system.views  # noqa: F401, E402
