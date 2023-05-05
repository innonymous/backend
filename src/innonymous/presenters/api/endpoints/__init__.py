from fastapi import APIRouter

__all__ = ("router",)

router = APIRouter()

from innonymous.presenters.api.endpoints.chats import router as chats  # noqa: E402
from innonymous.presenters.api.endpoints.events import router as events  # noqa: E402
from innonymous.presenters.api.endpoints.messages import router as messages  # noqa: E402
from innonymous.presenters.api.endpoints.sessions import router as sessions  # noqa: E402
from innonymous.presenters.api.endpoints.system import router as system  # noqa: E402

router.include_router(chats)
router.include_router(events)
router.include_router(messages)
router.include_router(sessions)
router.include_router(system)
