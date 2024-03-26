import pytest
from httpx import AsyncClient

from fastapi import status

__all__ = ("test_system_status",)


@pytest.mark.skip(reason="may be unnecessary or not viable")
async def test_system_status(api_client: AsyncClient) -> None:
    response = await api_client.get("v2/system/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
