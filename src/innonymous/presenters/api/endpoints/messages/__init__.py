from fastapi import APIRouter

router = APIRouter(tags=["messages"], prefix="/chats/{chat}")

__all__ = ("router",)

# Import views.
import innonymous.presenters.api.endpoints.messages.views  # noqa: F401, E402
