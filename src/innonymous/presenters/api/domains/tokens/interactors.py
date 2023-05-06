from innonymous.presenters.api.data.repositories.tokens import TokensRepository
from innonymous.presenters.api.domains.tokens.entities import TokenEntity

__all__ = ("TokensInteractor",)


class TokensInteractor:
    def __init__(self, repository: TokensRepository) -> None:
        self.__repository = repository

    def decode(self, token: str, *, audience: str | None = None) -> TokenEntity:
        return self.__repository.decode(token, audience=audience)

    def encode(self, entity: TokenEntity) -> str:
        return self.__repository.encode(entity)
