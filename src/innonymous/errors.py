import sys
import traceback
from typing import Any, TypeVar

__all__ = ("InnonymousError", "InnonymousTimeoutError")

Error = TypeVar("Error", bound="InnonymousError")


class InnonymousError(Exception):
    __message__ = "Unknown error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__()
        self._traceback = traceback.format_exc() if sys.exc_info()[0] is not None else ""
        self._attributes: dict[str, Any] = {"message": message if message is not None else self.__message__}

    @property
    def traceback(self) -> str:
        return self._traceback

    @property
    def message(self) -> str:
        return self._attributes["message"]

    def with_updated_traceback(self: Error) -> Error:
        updated = self.__class__()
        updated._attributes = self._attributes
        return updated

    def to_dict(self, *, include_traceback: bool = True) -> dict[str, Any]:
        serialized = {"alias": self.__class__.__name__, "attributes": self._attributes}

        if include_traceback:
            serialized["traceback"] = self._traceback

        return serialized

    def __str__(self) -> str:
        return "".join(f"<{key}: {value}>" for key, value in self._attributes.items())


class InnonymousTimeoutError(InnonymousError):
    __message__ = "Timeout occurred."

    def __init__(self, timeout: float | None = None, *, message: str | None = None) -> None:
        super().__init__(message)
        self._attributes["timeout"] = timeout

    @property
    def timeout(self) -> float | None:
        return self._attributes["timeout"]
