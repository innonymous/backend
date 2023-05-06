from fastapi import APIRouter

router = APIRouter(tags=["users"], prefix="/users")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.users.views  # noqa: F401, E402
