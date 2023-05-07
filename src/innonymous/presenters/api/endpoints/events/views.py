from dataclasses import asdict
from typing import Any, AsyncIterator

from pydantic import parse_obj_as
from sse_starlette import EventSourceResponse

from innonymous.presenters.api.application import innonymous
from innonymous.presenters.api.endpoints.events import router
from innonymous.presenters.api.endpoints.events.schemas import EventSchema

__all__ = ("get",)


@router.get("", response_class=EventSourceResponse)
async def get() -> EventSourceResponse:
    async def _iterator() -> AsyncIterator[dict[str, Any]]:
        async with innonymous.subscribe_on_events() as iterator:
            async for entity in iterator:
                event: EventSchema = parse_obj_as(EventSchema, asdict(entity))  # type: ignore[arg-type]
                yield {"event": event.type, "data": event.json(exclude={"type"})}

    return EventSourceResponse(_iterator())
