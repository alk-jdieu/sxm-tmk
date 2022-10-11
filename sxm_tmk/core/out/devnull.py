from typing import Any, Optional

from sxm_tmk.core.out.type import BackEndBase


class NullBackEnd(BackEndBase):
    def __init__(self):
        super(NullBackEnd, self).__init__()
        self._cache["progress"] = NullProgress
        self._cache["status"] = NullStatus

    def write(self, _) -> None:
        pass

    def info(self, msg: str, indent: Optional[str] = None) -> None:
        pass

    def debug(self, msg: str, indent: Optional[str] = None) -> None:
        pass

    def error(self, msg: str, indent: Optional[str] = None) -> None:
        pass

    def warning(self, msg: str, indent: Optional[str] = None) -> None:
        pass

    def build_progress(self) -> Any:
        return self.build("progress")

    def build_status(self, message: str) -> Any:
        return self.build("status", message)


class NullProgress:
    def __init__(self):
        pass

    def add_task(self, *args, **kwargs) -> int:
        return 0

    def update(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc, tb, value):
        pass


class NullStatus:
    def __init__(self, _):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc, tb, value):
        pass
