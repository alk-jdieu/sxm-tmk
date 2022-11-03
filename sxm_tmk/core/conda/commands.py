import contextlib
import subprocess
from typing import List, Optional


class Executable:
    def __init__(self, name: str):
        self.__executable: str = name

    @property
    def name(self) -> str:
        return self.__executable

    def run_in_executor(self, *args) -> str:
        return subprocess.check_output([self.name, *args], stderr=subprocess.DEVNULL).decode("utf8")


class Conda(Executable):
    def __init__(self):
        super(Conda, self).__init__("conda")

    def version(self) -> Optional[str]:
        with contextlib.suppress(subprocess.SubprocessError):
            output = self.run_in_executor("--version")
            if output:
                return output.split("\n")[0]
        return None


class Mamba(Executable):
    def __init__(self):
        super(Mamba, self).__init__("mamba")

    def version(self) -> Optional[str]:
        with contextlib.suppress(subprocess.SubprocessError):
            output = self.run_in_executor("--version")
            if output:
                return output.split("\n")[0]
        return None


class CondaSearch(Conda):
    def __init__(self, channels: Optional[List[str]] = None, use_index: bool = False):
        super(CondaSearch, self).__init__()
        self.use_index = use_index
        self.channels = channels or []

    def execute(self, pkg: str) -> Optional[str]:
        with contextlib.suppress(subprocess.CalledProcessError):
            channels = [f"-c {channel}" for channel in self.channels]
            return self.run_in_executor(
                "search",
                "--use-index-cache" if self.use_index else "",
                "--json",
                *channels,
                pkg,
            )
        return None


class MambaSearch(Conda):
    def __init__(self, channels: Optional[List[str]] = None, use_index: bool = False):
        super().__init__()
        self.use_index = use_index
        self.channels = channels or []

    def execute(self, pkg: str) -> Optional[str]:
        with contextlib.suppress(subprocess.CalledProcessError):
            channels = [f"-c {channel}" for channel in self.channels]
            return self.run_in_executor(
                "search",
                "--use-index-cache" if self.use_index else "",
                "--json",
                *channels,
                pkg,
            )
        return None
