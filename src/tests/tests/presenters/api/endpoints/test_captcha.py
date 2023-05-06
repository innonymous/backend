import pytest
from httpx import AsyncClient

from fastapi import status

from tests.utils import solve_captcha

__all__ = ("test_get_and_solve_captcha",)


@pytest.mark.it("Get captcha and brute force it.")
async def test_get_and_solve_captcha(api_client: AsyncClient) -> None:
    from innonymous.presenters.api.application import settings

    response = await api_client.get("v2/captcha")
    assert response.status_code == status.HTTP_200_OK

    body = response.json()
    assert body["image"].startswith("data:image/jpeg;base64,")

    # Try to solve the captcha.
    solve_captcha(settings.JWT_KEY.encode(), body["token"])
