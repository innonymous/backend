from fastapi import APIRouter

router = APIRouter(tags=["events"], prefix="/events")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.events.views  # noqa: F401, E402
