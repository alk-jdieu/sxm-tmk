import abc
from typing import Any, Dict, Optional


class Singleton(type):
    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BackEndBase:
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def build(self, backend_key: str, *args, **kwargs) -> Optional[Any]:
        try:
            return self._cache[backend_key](*args, **kwargs)
        except KeyError:
            return None

    @abc.abstractmethod
    def write(self, message: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def info(self, msg: str, indent: Optional[str] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def debug(self, msg: str, indent: Optional[str] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def error(self, msg: str, indent: Optional[str] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def warning(self, msg: str, indent: Optional[str] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def build_progress(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def build_status(self, message: str) -> Any:
        raise NotImplementedError
