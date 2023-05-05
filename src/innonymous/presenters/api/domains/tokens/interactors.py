from innonymous.presenters.api.data.repositories.tokens import TokensRepository
from innonymous.presenters.api.domains.tokens.entities import TokenEntity

__all__ = ("TokensInteractor",)


class TokensInteractor:
    def __init__(self, repository: TokensRepository) -> None:
        self.__repository = repository

    def get(self, token: str, *, audience: str | None = None) -> TokenEntity:
        return self.__repository.get(token, audience=audience)

    def create(self, entity: TokenEntity) -> str:
        return self.__repository.create(entity)
