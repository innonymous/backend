from fastapi import APIRouter

router = APIRouter(tags=["sessions"], prefix="/sessions")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.sessions.views  # noqa: F401, E402
