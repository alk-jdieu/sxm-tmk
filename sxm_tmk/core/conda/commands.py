import contextlib
import json
import pathlib
import subprocess
from typing import List, Optional


class Executable:
    def __init__(self, name: str):
        self.__executable: str = name

    @property
    def name(self) -> str:
        return self.__executable

    def run_in_executor(self, *args) -> str:
        command = list(filter(lambda x: x, [self.name, *args]))
        return subprocess.check_output(command, stderr=subprocess.DEVNULL).decode("utf8")


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


class MambaSearch(Mamba):
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


class MambaEnv(Mamba):
    def __init__(self):
        super().__init__()

    def fetch(self, only_envs: bool = True) -> List[str]:
        with contextlib.suppress(subprocess.CalledProcessError):
            data = self.run_in_executor(
                "env",
                "list",
                "--json",
            )
            try:
                j = json.loads(data)
                if only_envs:
                    j = j.get("envs", [])
                return j
            except json.JSONDecodeError:
                return []
        return []

    def exists(self, env_name: str) -> bool:
        return all([pathlib.Path(p).name != env_name for p in self.fetch(only_envs=True)])


class CondaEnv(Conda):
    def __init__(self):
        super().__init__()

    def fetch(self, only_envs: bool = True) -> List[str]:
        with contextlib.suppress(subprocess.CalledProcessError):
            data = self.run_in_executor(
                "env",
                "list",
                "--json",
            )
            try:
                j = json.loads(data)
                if only_envs:
                    j = j.get("envs", [])
                return j
            except json.JSONDecodeError:
                return []
        return []

    def exists(self, env_name: str) -> bool:
        return all([pathlib.Path(p).name != env_name for p in self.fetch(only_envs=True)])
