import contextlib
import os
import pathlib
import stat
import subprocess
from os import getcwd
from typing import List, Optional


class BashScript:
    def __init__(
        self, script: List[str], name: str = "script.sh", exit_on_error: bool = True, echo_statement: bool = False
    ):
        self.__script = script
        self.__script_name = name
        self.__exec_info: Optional[subprocess.CompletedProcess] = None
        self.__behaviour_exit_on_error = exit_on_error
        self.__behaviour_echo_statement = echo_statement

    def _shebang(self):
        if self.__behaviour_exit_on_error and self.__behaviour_echo_statement:
            self.__script.insert(0, "set -xe")
        elif self.__behaviour_exit_on_error and not self.__behaviour_echo_statement:
            self.__script.insert(0, "set -e")
        elif not self.__behaviour_exit_on_error and self.__behaviour_echo_statement:
            self.__script.insert(0, "set -x")
        self.__script.insert(0, "")
        self.__script.insert(0, "#!/opt/homebrew/bin/bash")

    def _write(self):
        p = pathlib.Path(getcwd()) / self.__script_name
        if not p.parent.exists():
            p.parent.mkdir(exist_ok=True, parents=True)
        p.touch()
        with p.open("w") as f:
            for line in self.__script:
                f.write(line + "\n")

    def run(self, timeout: Optional[int] = None) -> int:
        self._shebang()
        self._write()
        exec_path = f"{pathlib.Path(getcwd()).as_posix()}/./{self.__script_name}"
        file_path = pathlib.Path(getcwd()) / self.__script_name
        with contextlib.suppress(subprocess.TimeoutExpired):
            os.chmod(file_path.as_posix(), stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC | stat.S_IRUSR | stat.S_IRGRP)
            self.__exec_info = subprocess.run([exec_path], shell=True, capture_output=True, timeout=timeout)
        if self.__exec_info is None:
            self.__exec_info = subprocess.CompletedProcess(
                args=exec_path, returncode=100, stdout=b"", stderr=b"Timed out\n"
            )
        return self.__exec_info.returncode

    @property
    def return_code(self) -> int:
        if self.__exec_info:
            return self.__exec_info.returncode
        return 0

    @property
    def stdout(self) -> List[str]:
        if self.__exec_info:
            return self.__exec_info.stdout.decode("utf-8").split("\n")
        return []

    @property
    def stderr(self) -> List[str]:
        if self.__exec_info:
            return self.__exec_info.stderr.decode("utf-8").split("\n")
        return []
