import contextlib
import os
import pathlib
import stat
import subprocess
import tempfile
from os import getcwd
from typing import List, Optional


class ExecutionDir:
    def __init__(self, use_tempdir: bool = True, force_dir: Optional[pathlib.Path] = None):
        self.__use_temp_dir = use_tempdir
        self.__force_dir = force_dir
        self.__cwd: pathlib.Path = pathlib.Path.cwd()

    def __enter__(self):
        if self.__force_dir is not None:
            use_dir = self.__force_dir
        else:
            use_dir = pathlib.Path(tempfile.gettempdir())
        if not use_dir.exists():
            use_dir.mkdir(parents=True, exist_ok=True)  # We do not want errors to pop out
        self.__cwd: pathlib.Path = pathlib.Path.cwd()
        os.chdir(use_dir.as_posix())

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.__cwd.as_posix())


class BashScript:
    def __init__(
        self, script: List[str], name: str = "script.sh", exit_on_error: bool = True, echo_statement: bool = False
    ):
        self.__script = script
        self.__script_name = name
        self.__exec_info: Optional[subprocess.CompletedProcess] = None
        self.__behaviour_exit_on_error = exit_on_error
        self.__behaviour_echo_statement = echo_statement
        self.__timed_out: Optional[bool] = None

    def _shebang(self):
        if self.__behaviour_exit_on_error and self.__behaviour_echo_statement:
            self.__script.insert(0, "set -xe")
        elif self.__behaviour_exit_on_error and not self.__behaviour_echo_statement:
            self.__script.insert(0, "set -e")
        elif not self.__behaviour_exit_on_error and self.__behaviour_echo_statement:
            self.__script.insert(0, "set -x")
        self.__script.insert(0, "")
        # Let's find the most appropriate path to bash
        path_to_bash = "/usr/bin/env bash"
        with contextlib.suppress(subprocess.SubprocessError):
            run_info = subprocess.Popen(["command", "-v", "bash"], stdout=subprocess.PIPE)
            out, _ = run_info.communicate()
            if run_info.returncode == 0:
                out = [line.decode("utf8") for line in out.split()]
                out = list(filter(lambda line: line, out))
                with contextlib.suppress(IndexError):
                    path_to_bash = out[0]
        self.__script.insert(0, f"#!{path_to_bash}")

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
            self.__timed_out = False
        if self.__exec_info is None:
            self.__timed_out = True
            self.__exec_info = subprocess.CompletedProcess(
                args=exec_path, returncode=100, stdout=b"", stderr=b"Timed out\n"
            )
        return self.__exec_info.returncode

    def reset(self):
        self.__timed_out = None
        self.__exec_info = None

    @property
    def has_completed(self) -> bool:
        return not self.__timed_out if self.__timed_out is not None else False

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
