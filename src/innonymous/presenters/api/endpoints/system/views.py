from innonymous.presenters.api.endpoints.system import router
from innonymous.presenters.api.endpoints.system.schemas import SystemStatusOKSchema

__all__ = ("status",)


@router.get("/status", response_model=SystemStatusOKSchema, description="Returns OK if system is online.")
async def status() -> SystemStatusOKSchema:
    return SystemStatusOKSchema()
