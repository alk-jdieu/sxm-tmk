from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress
from rich.status import Status

from sxm_tmk.core.out.type import BackEndBase


class RichBackEnd(BackEndBase):
    def __init__(self):
        super(RichBackEnd, self).__init__()
        self.__impl = Console()
        self._cache["progress"] = Progress
        self._cache["status"] = Status

    def write(self, message) -> None:
        self.__impl.print(message)

    def info(self, msg: str, indent: Optional[str] = None) -> None:
        self.__impl.print(f"{indent}{msg}")

    def debug(self, msg: str, indent: Optional[str] = None) -> None:
        self.__impl.print(f"{indent}[grey]{msg}[/grey]")

    def error(self, msg: str, indent: Optional[str] = None) -> None:
        self.__impl.print(f"{indent}[red]{msg}[/red]")

    def warning(self, msg: str, indent: Optional[str] = None) -> None:
        self.__impl.print(f"{indent}[bold]{msg}[/bold]")

    def build_progress(self) -> Any:
        return self.build("progress")

    def build_status(self, message) -> Any:
        return self.build("status", message, spinner="simpleDotsScrolling")
