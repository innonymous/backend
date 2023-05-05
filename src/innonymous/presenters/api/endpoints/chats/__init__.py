from fastapi import APIRouter

router = APIRouter(tags=["chats"], prefix="/chats")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.chats.views  # noqa: F401, E402
